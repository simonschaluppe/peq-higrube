"""Area-preserving extrapolation of Austrian building-stock GFZ distributions.

Reference building samples: Vienna for Vienna; Salzburg for all other provinces.
Regional statistics are NGF by province, storey class and use. Missing strata are
NEVER silently omitted. Explicit fallback estimates are separately flagged.

Run: python gfz_hydrator.py --buildings rohdaten_python.xlsx \
    --statistics GFZ_Analyse_AT_Wien.xlsx --out results --fallback vienna
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

PROVINCES = (
    "Burgenland", "Kärnten", "Niederösterreich", "Oberösterreich", "Salzburg",
    "Steiermark", "Tirol", "Vorarlberg", "Wien",
)
STOREYS = ("1", "2", "3", "4", "5", "6-10", "11+")
USES = (
    "Hotels o.Ä.", "Büronutzung", "Groß- und Einzelhandelsgebäude",
    "Verkehrs- und Nachrichtenwesen", "Industrie und Lagerung",
    "Kultur, Freizeit, Bildung und Gesundheit", "Gemeinschaftsgebäude",
    "Mehrfamilienhaus", "Ein- und Zweifamilienhäuser",
)
TARGET_COLUMNS = ["NUTS", "GK", *USES]
SAMPLE_COLUMNS = ["Bundesland", "GK", "GWR_Nutzung", "GFZ", "BGF"]


def norm_gk(value: object) -> str:
    """Unify '6 bis 10'/'6-10'/6010 and Excel's int/float classes."""
    text = str(value).strip().lower()
    text = " ".join(text.split())
    if text in {"6 bis 10", "6-10", "6–10", "6010", "6.0 bis 10.0"}:
        return "6-10"
    if text in {"11+", "11 und mehr", "11 oder mehr", "11plus"}:
        return "11+"
    if text.endswith(".0"):
        text = text[:-2]
    if text in STOREYS:
        return text
    raise ValueError(f"Unknown storey class: {value!r}")


def norm_usage(value: object) -> str:
    text = str(value).strip()
    if text in {"Mehrfamilienhaus klein", "Mehrfamilienhaus groß"}:
        return "Mehrfamilienhaus"
    return text


def read_table(path: str | Path, sheet_name: str) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, dtype={"GK": str}, low_memory=False)
    if path.suffix.lower() == ".xlsx":
        return pd.read_excel(path, sheet_name=sheet_name, dtype={"GK": str})
    raise ValueError(f"Expected CSV or XLSX input: {path}")


def read_samples(path: str | Path, *, max_gfz: float) -> tuple[pd.DataFrame, dict]:
    data = read_table(path, "Rohdaten")
    missing = set(SAMPLE_COLUMNS) - set(data.columns)
    if missing:
        raise ValueError(f"Building data missing columns: {sorted(missing)}")
    data = data.loc[:, SAMPLE_COLUMNS].copy()
    data["GK"] = data["GK"].map(norm_gk)
    data["GWR_Nutzung"] = data["GWR_Nutzung"].map(norm_usage)
    data["GFZ"] = pd.to_numeric(data["GFZ"], errors="coerce")
    data["BGF"] = pd.to_numeric(data["BGF"], errors="coerce")
    shape_before = len(data)
    # Unrepresented usage classes are intentionally excluded from the sample,
    # but their counts are recorded. No target use class is dropped.
    other_use = ~data["GWR_Nutzung"].isin(USES)
    invalid_numeric = (~np.isfinite(data["GFZ"])) | (~np.isfinite(data["BGF"])) | (data["GFZ"] <= 0) | (data["BGF"] <= 0)
    out_of_range = data["GFZ"] > max_gfz
    unexpected_region = ~data["Bundesland"].isin(("Wien", "Salzburg"))
    dropped = other_use | invalid_numeric | out_of_range | unexpected_region
    report = {
        "sample_rows_original": shape_before,
        "sample_rows_usable": int((~dropped).sum()),
        "excluded_other_uses": int(other_use.sum()),
        "excluded_invalid_numeric": int(invalid_numeric.sum()),
        "excluded_gfz_above_max": int(out_of_range.sum()),
        "excluded_unexpected_region": int(unexpected_region.sum()),
        "excluded_bgf_m2_total": float(data.loc[dropped, "BGF"].where(np.isfinite(data["BGF"]), 0).sum()),
        "sample_gfz_max": float(data["GFZ"].max()),
    }
    data = data.loc[~dropped].copy()
    return data, report


def read_statistics(path: str | Path, *, ngf_per_bgf: float) -> tuple[pd.DataFrame, dict]:
    stats = read_table(path, "python")
    missing = set(TARGET_COLUMNS) - set(stats.columns)
    if missing:
        raise ValueError(f"Statistics missing columns: {sorted(missing)}")
    # Original workbook also carries historical summary rows. They overlap the
    # nine provinces and must not enter the allocation or AT reconciliation.
    aggregate_mask = stats['NUTS'].isin(['AT ohne Wien und Salzburg', 'Alles'])
    excluded_aggregates = stats.loc[aggregate_mask, 'NUTS'].value_counts().to_dict()
    stats = stats.loc[~aggregate_mask].copy()
    extras = set(stats["NUTS"].dropna().astype(str)) - {*PROVINCES, "AT"}
    if extras:
        raise ValueError(f"Unknown geographic entries: {sorted(extras)}")
    stats["GK"] = stats["GK"].map(norm_gk)
    if stats.duplicated(["NUTS", "GK"]).any():
        raise ValueError("Duplicate statistics rows for the same province and GK")
    missing_pairs = {(province, gk) for province in (*PROVINCES, "AT") for gk in STOREYS} - set(zip(stats["NUTS"], stats["GK"]))
    if missing_pairs:
        raise ValueError(f"Statistics missing province/storey rows: {sorted(missing_pairs)}")
    for u in USES:
        stats[u] = pd.to_numeric(stats[u], errors="raise").fillna(0)
    if (stats[list(USES)] < 0).any().any():
        raise ValueError("Negative statistical areas found")
    long = stats[TARGET_COLUMNS].melt(["NUTS", "GK"], var_name="GWR_Nutzung", value_name="NGF_m2")
    # Statistics include AT aggregates solely for validation, not for national scaling.
    national = long.loc[long["NUTS"] == "AT", ["GK", "GWR_Nutzung", "NGF_m2"]].set_index(["GK", "GWR_Nutzung"])["NGF_m2"]
    provinces = long.loc[long["NUTS"].isin(PROVINCES)].copy()
    regional = provinces.groupby(["GK", "GWR_Nutzung"])["NGF_m2"].sum()
    discrepancy = regional.sub(national, fill_value=0)
    if not np.allclose(discrepancy.to_numpy(), 0, rtol=0, atol=0.01):
        offenders = discrepancy.loc[discrepancy.abs() > 0.01].head(8).to_dict()
        raise ValueError(f"Provincial statistics do not add up to 'AT': {offenders}")
    provinces["BGF_target_m2"] = provinces["NGF_m2"] / ngf_per_bgf
    meta = {
        "statistics_ngf_total_m2": float(national.sum()),
        "statistics_bgf_total_m2": float(national.sum() / ngf_per_bgf),
        "national_minus_provinces_ngf_m2": float(discrepancy.abs().sum()),
        "ngf_per_bgf_assumption": ngf_per_bgf,
        "excluded_legacy_aggregate_rows": excluded_aggregates,
    }
    return provinces, meta


def prepare_groups(samples: pd.DataFrame) -> dict:
    return {k: group for k, group in samples.groupby(["Bundesland", "GK", "GWR_Nutzung"], sort=False)}


def choose_reference(groups: dict, province: str, gk: str, usage: str, *, minimum: int, fallback: str) -> tuple[tuple, str]:
    main_region = "Wien" if province == "Wien" else "Salzburg"
    requested = (main_region, gk, usage)
    if len(groups.get(requested, ())) >= minimum:
        return requested, "reference-exact"
    if fallback == "error":
        raise ValueError(f"Insufficient reference buildings in {requested}; found {len(groups.get(requested,()))}, minimum {minimum}")
    # Explicit replacement hierarchy; no substitutions within statistics groups.
    # 1) Vienna exact class and use, irrespective of target province.
    wien = ("Wien", gk, usage)
    if len(groups.get(wien, ())) >= minimum:
        return wien, "fallback-vienna-exact"
    # 2) Same-use nearest storey class in preferred region, then Vienna.
    for region in list(dict.fromkeys([main_region, "Wien"])):
        candidates = [(abs(STOREYS.index(gk) - STOREYS.index(gg)), gg)
                      for gg in STOREYS if len(groups.get((region, gg, usage), ())) >= minimum]
        if candidates:
            _, nearest = min(candidates)
            return (region, nearest, usage), f"fallback-{region.lower()}-nearest-storey"
    raise ValueError(f"No sample can represent {province}/{gk}/{usage} with n >= {minimum}")


def estimate_distribution(group: pd.DataFrame, centers: np.ndarray, *, method: str) -> tuple[np.ndarray, str]:
    gfz = group["GFZ"].to_numpy(dtype=float)
    weights = group["BGF"].to_numpy(dtype=float)
    if method == "histogram" or len(np.unique(gfz)) < 2:
        spacing = float(centers[1] - centers[0])
        edges = np.concatenate([[centers[0] - spacing / 2], centers + spacing / 2])
        probabilities, _ = np.histogram(gfz, bins=edges, weights=weights)
        estimator = "bgf-weighted-histogram"
    else:
        kde = gaussian_kde(gfz, weights=weights, bw_method="scott")
        probabilities = kde(centers)
        estimator = "bgf-weighted-kde-scott"
    total = float(probabilities.sum())
    if not np.isfinite(total) or total <= 0:
        raise ValueError("KDE/histogram produced no finite positive probability")
    probabilities = probabilities / total
    if (probabilities < 0).any() or not np.isclose(probabilities.sum(), 1, atol=1e-9):
        raise AssertionError("Invalid reference distribution")
    return probabilities, estimator


def calculate(samples: pd.DataFrame, targets: pd.DataFrame, *, gfz_step: float, gfz_max: float,
              min_samples: int, fallback: str, method: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    groups = prepare_groups(samples)
    nbin = round(gfz_max / gfz_step)
    if nbin <= 0 or not np.isclose(nbin * gfz_step, gfz_max):
        raise ValueError("gfz_max must be a positive multiple of gfz_step")
    centers = (np.arange(nbin) + 0.5) * gfz_step
    probability_cache = {}
    cells = []
    allocations = []
    for rec in targets.itertuples(index=False):
        if rec.BGF_target_m2 <= 0:
            continue
        source, status = choose_reference(groups, rec.NUTS, rec.GK, rec.GWR_Nutzung,
                                          minimum=min_samples, fallback=fallback)
        if source not in probability_cache:
            probability_cache[source] = estimate_distribution(groups[source], centers, method=method)
        probabilities, estimator = probability_cache[source]
        cell_id = f"{rec.NUTS}|{rec.GK}|{rec.GWR_Nutzung}"
        allocated = probabilities * rec.BGF_target_m2
        cells.append({
            "cell_id": cell_id, "Bundesland": rec.NUTS, "GK": rec.GK,
            "GWR_Nutzung": rec.GWR_Nutzung, "NGF_stat_m2": rec.NGF_m2,
            "BGF_target_m2": rec.BGF_target_m2,
            "BGF_allocated_m2": float(allocated.sum()),
            "delta_m2": float(allocated.sum() - rec.BGF_target_m2),
            "reference_region": source[0], "reference_gk": source[1],
            "status": status, "n_reference_buildings": len(groups[source]),
            "sample_reference_bgf_m2": float(groups[source]["BGF"].sum()),
            "estimate_method": estimator,
            "expected_gfz": float(np.dot(centers, probabilities)),
        })
        allocations.extend({"cell_id": cell_id, "Bundesland": rec.NUTS,
                            "GK": rec.GK, "GWR_Nutzung": rec.GWR_Nutzung,
                            "GFZ": float(round(center, 10)), "BGF_m2": float(area)}
                           for center, area in zip(centers, allocated) if area > 0)
    detail = pd.DataFrame(allocations)
    audit = pd.DataFrame(cells)
    assert not detail.empty and not audit.empty, "No output generated"
    if not np.allclose(audit["BGF_allocated_m2"], audit["BGF_target_m2"], rtol=1e-12, atol=1e-5):
        raise AssertionError("Some cells do not conserve their allocated BGF")
    if not np.isclose(detail["BGF_m2"].sum(), targets["BGF_target_m2"].sum(), rtol=1e-12, atol=1e-4):
        raise AssertionError("National allocated floor area does not equal national BGF target")
    return detail, audit


def run(args: argparse.Namespace) -> dict:
    samples, sample_meta = read_samples(args.buildings, max_gfz=args.gfz_max)
    targets, stats_meta = read_statistics(args.statistics, ngf_per_bgf=args.ngf_per_bgf)
    # Preflight coverage report, saved even if strict mode fails.
    groups = prepare_groups(samples)
    coverage = []
    for rec in targets.itertuples(index=False):
        if rec.BGF_target_m2 <= 0:
            continue
        reg = "Wien" if rec.NUTS == "Wien" else "Salzburg"
        available = len(groups.get((reg, rec.GK, rec.GWR_Nutzung), ()))
        coverage.append({"Bundesland": rec.NUTS, "GK": rec.GK, "GWR_Nutzung": rec.GWR_Nutzung,
                         "BGF_target_m2": rec.BGF_target_m2,
                         "primary_reference_region": reg, "primary_n": available,
                         "sufficient": available >= args.min_samples})
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    coverage_df = pd.DataFrame(coverage)
    coverage_df.to_csv(out / "reference_coverage.csv", index=False)
    detail, audit = calculate(samples, targets, gfz_step=args.gfz_step, gfz_max=args.gfz_max,
                              min_samples=args.min_samples, fallback=args.fallback, method=args.method)
    detail.to_csv(out / "gfz_distribution_by_province_use_storeys.csv", index=False)
    audit.to_csv(out / "allocation_audit.csv", index=False)
    detail.groupby(["Bundesland", "GFZ"], as_index=False)["BGF_m2"].sum().to_csv(
        out / "gfz_distribution_by_province.csv", index=False)
    detail.groupby(["GFZ", "GWR_Nutzung"], as_index=False)["BGF_m2"].sum().to_csv(
        out / "gfz_distribution_austria_by_use.csv", index=False)
    totals = audit.groupby("Bundesland", as_index=False)[["BGF_target_m2", "BGF_allocated_m2", "delta_m2"]].sum()
    totals.to_csv(out / "province_totals.csv", index=False)
    fb = audit.loc[audit["status"] != "reference-exact"]
    report = {
        "description": "AT GFZ: Vienna sample for Vienna, Salzburg sample elsewhere, explicitly flagged fallbacks",
        "GFZ_bins": {"step": args.gfz_step, "max": args.gfz_max, "centers": True},
        "input_files": {"buildings": str(args.buildings), "statistics": str(args.statistics)},
        "input_sha256": {name: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                         for name, path in [('buildings', args.buildings), ('statistics', args.statistics)]},
        "options": {"fallback": args.fallback, "method": args.method, "min_samples": args.min_samples},
        **sample_meta, **stats_meta,
        "n_positive_statistical_cells": len(coverage_df),
        "n_fallback_cells": len(fb),
        "fallback_bgf_m2": float(fb["BGF_target_m2"].sum()),
        "fallback_share_of_total_bgf": float(fb["BGF_target_m2"].sum() / stats_meta["statistics_bgf_total_m2"]),
        "allocated_bgf_m2": float(detail["BGF_m2"].sum()),
        "total_allocation_residual_m2": float(detail["BGF_m2"].sum() - stats_meta["statistics_bgf_total_m2"]),
        "fallback_by_type": {str(k): float(v) for k, v in fb.groupby("status")["BGF_target_m2"].sum().items()},
    }
    (out / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def cli() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--buildings", required=True, type=Path, help="Rohdaten sheet of rohdaten_python.xlsx, or CSV")
    p.add_argument("--statistics", required=True, type=Path, help="'python' sheet of GFZ_Analyse_AT_Wien.xlsx, or CSV")
    p.add_argument("--out", default=Path("outputs/gfz_at"), type=Path)
    p.add_argument("--ngf-per-bgf", default=0.8, type=float, help="Explicit estimate, not inferred from source (default 0.8)")
    p.add_argument("--gfz-step", default=0.1, type=float)
    p.add_argument("--gfz-max", default=20.0, type=float)
    p.add_argument("--min-samples", default=5, type=int)
    p.add_argument("--method", choices=["kde", "histogram"], default="kde")
    p.add_argument("--fallback", choices=["error", "vienna"], default="error",
                   help="'vienna' explicitly substitutes Vienna exact cell or nearest-storey same-use reference")
    return p


def main() -> None:
    args = cli().parse_args()
    if not 0 < args.ngf_per_bgf <= 1:
        raise ValueError("Require 0 < NGF/BGF <= 1")
    if args.min_samples < 2:
        raise ValueError("Require at least 2 reference samples")
    summary = run(args)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
