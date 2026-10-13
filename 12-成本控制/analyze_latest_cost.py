# -*- coding: utf-8 -*-
import openpyxl,json,os,collections,math
path=r'C:\Users\Administrator\Desktop\华盛\成本核算汇总-标准成本 - 加工与自产.xlsx'
out=r'D:\AI-项目\12-成本控制\latest_cost_analysis.json'
w=openpyxl.load_workbook(path,data_only=True,read_only=True)
months=['4月','5月','6月','7月']
def num(x):
 try:return float(x or 0)
 except:return 0.0
def safe(v): return '' if v is None else str(v)
# fixed columns, 1-indexed -> zero-indexed
# name C=2, qty I=8, std_use P=15, actual_use Q=16, std_amt AS? 45? actual material AV? 47; labor BH? 59, mfg BU? 71, std cost BT?71? inspect: col72 standard total,73 actual total,74 std unit,75 actual unit,76 variance
rows=[]
for m in months:
 ws=w[m]
 for ridx,row in enumerate(ws.iter_rows(min_row=3,values_only=True),3):
  name=row[2]
  if not name or safe(name) in ('合计','汇总'): continue
  item={'month':m,'row':ridx,'name':safe(name),'code':safe(row[3]),'type':safe(row[4]),'qty':num(row[8]),'std_use':num(row[15]),'actual_use':num(row[16]),'std_mat':num(row[44]),'actual_mat':num(row[46]),'labor':num(row[59]),'mfg':num(row[70]),'std_cost':num(row[71]),'actual_cost':num(row[72]),'std_unit':num(row[73]),'actual_unit':num(row[74]),'variance_rate':num(row[75]),'note':safe(row[76])}
  item['use_diff']=item['actual_use']-item['std_use']; item['use_diff_pct']=item['use_diff']/item['std_use']*100 if item['std_use'] else None; item['variance_amt']=item['actual_cost']-item['std_cost']; item['material_diff_amt']=item['actual_mat']-item['std_mat']; item['actual_mat_per_kg']=item['actual_mat']/item['qty'] if item['qty'] else 0; item['actual_unit_calc']=item['actual_cost']/item['qty'] if item['qty'] else 0; rows.append(item)
# aggregate monthly
monthly={}
for m in months:
 rr=[x for x in rows if x['month']==m]; q=sum(x['qty'] for x in rr); st=sum(x['std_cost'] for x in rr); ac=sum(x['actual_cost'] for x in rr); sm=sum(x['std_mat'] for x in rr); am=sum(x['actual_mat'] for x in rr); la=sum(x['labor'] for x in rr); mf=sum(x['mfg'] for x in rr); su=sum(x['std_use'] for x in rr); au=sum(x['actual_use'] for x in rr)
 monthly[m]={'records':len(rr),'qty':q,'std_cost':st,'actual_cost':ac,'variance':ac-st,'variance_pct':(ac-st)/st*100 if st else 0,'std_unit':st/q if q else 0,'actual_unit':ac/q if q else 0,'std_mat':sm,'actual_mat':am,'labor':la,'mfg':mf,'std_use':su,'actual_use':au,'use_diff_pct':(au-su)/su*100 if su else 0,'material_diff_pct':(am-sm)/sm*100 if sm else 0,'material_pct':am/ac*100 if ac else 0}
# aggregate product
agg={}
for x in rows:
 a=agg.setdefault(x['name'],{'name':x['name'],'code':x['code'],'records':0,'qty':0,'std_cost':0,'actual_cost':0,'variance':0,'std_mat':0,'actual_mat':0,'labor':0,'mfg':0,'std_use':0,'actual_use':0,'months':[],'notes':[]})
 for k in ['qty','std_cost','actual_cost','std_mat','actual_mat','labor','mfg','std_use','actual_use']: a[k]+=x[k]
 a['records']+=1; a['variance']+=x['variance_amt']; a['months'].append(x['month']);
 if x['note']: a['notes'].append({'month':x['month'],'note':x['note'],'variance_rate':x['variance_rate'],'use_diff_pct':x['use_diff_pct']})
for a in agg.values():
 a['unit']=a['actual_cost']/a['qty'] if a['qty'] else 0; a['std_unit']=a['std_cost']/a['qty'] if a['qty'] else 0; a['variance_pct']=a['variance']/a['std_cost']*100 if a['std_cost'] else 0; a['material_diff']=a['actual_mat']-a['std_mat']; a['material_diff_pct']=a['material_diff']/a['std_mat']*100 if a['std_mat'] else 0; a['use_diff']=a['actual_use']-a['std_use']; a['use_diff_pct']=a['use_diff']/a['std_use']*100 if a['std_use'] else 0; a['cost_share']=a['actual_cost']/sum(z['actual_cost'] for z in agg.values())*100 if sum(z['actual_cost'] for z in agg.values()) else 0
products=sorted(agg.values(),key=lambda a:a['actual_cost'],reverse=True)
# abnormal by money and by rate
ab_money=sorted([x for x in rows if x['variance_amt']>0],key=lambda x:x['variance_amt'],reverse=True)
ab_rate=sorted([x for x in rows if x['variance_rate']>0.1 and x['qty']>=100],key=lambda x:x['variance_rate'],reverse=True)
use_ab=sorted([x for x in rows if x['use_diff_pct'] is not None and x['use_diff_pct']>10 and x['qty']>=100],key=lambda x:x['material_diff_amt'],reverse=True)
notes=[x for x in rows if x['note']]
result={'source':path,'months':months,'record_count':len(rows),'monthly':monthly,'products':products,'abnormal_money':ab_money[:30],'abnormal_rate':ab_rate[:30],'use_abnormal':use_ab[:30],'notes':notes,'counts':{'positive_variance_records':sum(x['variance_amt']>0 for x in rows),'negative_variance_records':sum(x['variance_amt']<0 for x in rows),'notes':len(notes),'use_gt10':sum(x['use_diff_pct'] is not None and x['use_diff_pct']>10 for x in rows),'actual_zero':sum(x['actual_cost']==0 for x in rows)}}
with open(out,'w',encoding='utf-8') as f: json.dump(result,f,ensure_ascii=False,indent=2)
print(out)
