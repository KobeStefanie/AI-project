# -*- coding: utf-8 -*-
import pickle,json,collections
D=r'D:\AI-项目\12-成本控制\months_data_correct.pkl'
out=r'D:\AI-项目\12-成本控制\deep_cost_analysis.json'
with open(D,'rb') as f: d=pickle.load(f)
ms=list(d.keys()); k=list(d[ms[0]][0].keys()); name,qty,mat,lab,mfg,cost,unit=k[0],k[2],k[3],k[4],k[5],k[6],k[7]
def f(x,key): return float(x.get(key,0) or 0)
def summary(rows):
 q=sum(f(x,qty) for x in rows); c=sum(f(x,cost) for x in rows); ma=sum(f(x,mat) for x in rows); la=sum(f(x,lab) for x in rows); mf=sum(f(x,mfg) for x in rows)
 return {'n':len(rows),'qty':q,'cost':c,'unit':c/q if q else 0,'material':ma,'labor':la,'mfg':mf,'material_pct':ma/c*100 if c else 0,'labor_pct':la/c*100 if c else 0,'mfg_pct':mf/c*100 if c else 0,'material_per_kg':ma/q if q else 0,'labor_per_kg':la/q if q else 0,'mfg_per_kg':mf/q if q else 0}
monthly={m:summary(d[m]) for m in ms}
agg=collections.defaultdict(lambda:{'n':0,'qty':0,'cost':0,'material':0,'labor':0,'mfg':0,'months':[]})
for m in ms:
 for x in d[m]:
  a=agg[x[name]]; a['n']+=1; a['qty']+=f(x,qty); a['cost']+=f(x,cost); a['material']+=f(x,mat); a['labor']+=f(x,lab); a['mfg']+=f(x,mfg); a['months'].append({'month':m,'qty':f(x,qty),'unit':f(x,unit),'material':f(x,mat)})
products=[]; total=sum(a['cost'] for a in agg.values())
for n,a in agg.items():
 a['unit']=a['cost']/a['qty'] if a['qty'] else 0; a['material_pct']=a['material']/a['cost']*100 if a['cost'] else 0; a['cost_share']=a['cost']/total*100 if total else 0; a['material_per_kg']=a['material']/a['qty'] if a['qty'] else 0; a['labor_per_kg']=a['labor']/a['qty'] if a['qty'] else 0; a['mfg_per_kg']=a['mfg']/a['qty'] if a['qty'] else 0; a['name']=n; products.append(a)
products.sort(key=lambda a:a['cost'],reverse=True)
valid={m:summary([x for x in d[m] if f(x,mat)>0 and f(x,qty)>=100]) for m in ms[-2:]}
for x in products: x.pop('months',None)
result={'fields':k,'monthly':monthly,'valid_7_8':valid,'missing_material':sum(f(x,mat)==0 for m in ms for x in d[m]),'small_qty':sum(f(x,qty)<100 for m in ms for x in d[m]),'record_count':sum(len(d[m]) for m in ms),'product_count':len(products),'products':products,'concentration':{'top2_share':sum(x['cost_share'] for x in products[:2]),'top5_share':sum(x['cost_share'] for x in products[:5]),'top10_share':sum(x['cost_share'] for x in products[:10])}}
with open(out,'w',encoding='utf-8') as f: json.dump(result,f,ensure_ascii=False,indent=2)
print(out)
