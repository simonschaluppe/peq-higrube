import fs from 'node:fs/promises';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';
const input=JSON.parse(await fs.readFile('.local/building-inputs.json','utf8'));
const wb=Workbook.create();
for (const [name, data] of Object.entries(input)) {
 const s=wb.worksheets.add(name); s.showGridLines=false;
 const rows=[data.columns,...data.data];
 const area=s.getRangeByIndexes(0,0,rows.length,data.columns.length);
 area.values=rows; area.format.font={name:'Arial',size:10};
 area.format.rowHeight=20; area.format.columnWidth=20;
 s.getRangeByIndexes(0,0,1,data.columns.length).format={fill:'#254766',font:{bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:48};
 s.getRangeByIndexes(0,0,rows.length,1).format.columnWidth=name==='Typen'||name==='Anwendungen'?49:28;
 area.format.verticalAlignment='center';
 s.freezePanes.freezeRows(1);
 if (name==='Typen') {
  s.getRange('B2:C901').setNumberFormat('0.00%');
  s.getRange('D2:E901').setNumberFormat('#,##0.0');
  s.getRange('F2:H901').setNumberFormat('0.0%');
  s.getRange('J2:S901').setNumberFormat('0.00');
  s.getRange('T2:W901').format.fill='#FFF2CC';
  s.getRange('T2:T901').setNumberFormat('#,##0.0');
  s.getRange('U2:U901').setNumberFormat('0.0%');
 }
 if (name==='Anwendungen') s.getRangeByIndexes(1,1,rows.length-1,data.columns.length-1).setNumberFormat('0.000');
 if (name==='GFZ_Zuordnung') {s.getRange('A1:A71').format.columnWidth=50;s.getRange('A2:A71').format.wrapText=true;s.getRange('A2:F71').format.rowHeight=45;s.getRange('C2:C71').setNumberFormat('0%');s.getRange('E2:E71').setNumberFormat('0%');}
 if (name==='Parameter') {s.getRange('D1:D9').format.columnWidth=85;s.getRange('D2:D9').format.wrapText=true;s.getRange('A2:D9').format.rowHeight=40;s.getRange('B2:C9').format.fill='#FFF2CC';}
 if (name==='PE_Faktoren') {s.getRange('C2:E15').format.fill='#FFF2CC';s.getRange('E1:E15').format.columnWidth=50;}
 if (name==='Woerterbuch') {s.getRange('A1:B60').format.columnWidth=38;s.getRange('B2:B60').format.wrapText=true;s.getRange('A2:D60').format.rowHeight=30;}
 if (name==='Hinweise') {s.getRange('B1:B9').format.columnWidth=105;s.getRange('B2:B9').format.wrapText=true;s.getRange('A2:B9').format.rowHeight=36;}
}
wb.recalculate();
console.log((await wb.inspect({kind:'table',range:'Typen!A1:F5',include:'values',tableMaxRows:5,tableMaxCols:6})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!',options:{useRegex:true,maxResults:20},summary:'Fehlerprüfung Reinschrift'})).ndjson);
for (const name of Object.keys(input)) {
 const end={Typen:'F7',Anwendungen:'F7',GFZ_Zuordnung:'F8',Parameter:'D9',PE_Faktoren:'E8',Woerterbuch:'D8',Hinweise:'B9'}[name];
 const preview=await wb.render({sheetName:name,range:`A1:${end}`,scale:1,format:'png'});
 await fs.writeFile(`.local/building-artifacts/${name}.png`,new Uint8Array(await preview.arrayBuffer()));
}
const file=await SpreadsheetFile.exportXlsx(wb);
await file.save('Berechnungen/gebaeudesektormodell/daten_gebauedesektor.xlsx');
console.log('Workbook exported');
