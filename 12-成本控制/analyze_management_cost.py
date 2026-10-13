import pickle,sys,statistics,math,json
sys.stdout.reconfigure(encoding='utf-8')
d=pickle.load(open(r'D:\AI-项目\12-成本控制\months_data_correct.pkl','rb'))
ms=list(d.keys())
def f(x,k): return float(x.get(k,0) or 0)
keys=list(d[ms[0]][0].keys()); name,qty,mat,lab,mfg,cost,unit=keys[0],keys[2],keys[3],keys[4],keys[5],keys[6],keys[7]
print('FIELDS',keys)
# month weighted stats
for m in ms:
 rows=d[m]; q=sum(f(x,qty) for x in rows); c=sum(f(x,cost) for x in rows); ma=sum(f(x,mat) for x in rows); la=sum(f(x,lab) for x in rows); mf=sum(f(x,mfg) for x in rows)
 print('MONTH',m,'n',len(rows),'qty',round(q,1),'cost_wan',round(c/10000,2),'unit',round(c/q,3),'mat_pct',round(ma/c*100,2),'lab_pct',round(la/c*100,2),'mfg_pct',round(mf/c*100,2),'mat_perkg',round(ma/q,3),'lab_perkg',round(la/q,3),'mfg_perkg',round(mf/q,3))
# product aggregate
agg={}
for m in ms:
 for x in d[m]:
  n=x[name]; a=agg.setdefault(n,{'n':0,'q':0,'c':0,'ma':0,'la':0,'mf':0,'months':[]})
  a['n']+=1; a['q']+=f(x,qty); a['c']+=f(x,cost); a['ma']+=f(x,mat); a['la']+=f(x,lab); a['mf']+=f(x,mfg); a['months'].append((m,f(x,qty),f(x,cost)/f(x,qty) if f(x,qty) else 0,f(x,mat)))
print('PRODUCT_COUNT',len(agg))
rows=[]
for n,a in agg.items():
 a['unit']=a['c']/a['q'] if a['q'] else 0; a['mat_unit']=a['ma']/a['q'] if a['q'] else 0; a['lab_unit']=a['la']/a['q'] if a['q'] else 0; a['mfg_unit']=a['mf']/a['q'] if a['q'] else 0; a['share']=a['c']/sum(z['c'] for z in agg.values())*100
 rows.append((n,a))
print('TOP_COST_CONTRIBUTION')
for n,a in sorted(rows,key=lambda z:z[1]['c'],reverse=True)[:12]: print(n, 'n',a['n'],'q',round(a['q']), 'unit',round(a['unit'],2),'cost_wan',round(a['c']/10000,2),'share',round(a['share'],2),'mat_unit',round(a['mat_unit'],2))
print('TOP_HIGH_UNIT_MIN1000')
for n,a in sorted([z for z in rows if z[1]['q']>=1000],key=lambda z:z[1]['unit'],reverse=True)[:12]: print(n,'q',round(a['q']),'unit',round(a['unit'],2),'cost_wan',round(a['c']/10000,2),'mat_pct',round(a['ma']/a['c']*100,1))
print('TOP_RISK_SMALL_OR_MISSING')
for n,a in sorted(rows,key=lambda z:z[1]['c'],reverse=True)[:20]:
 miss=sum(1 for mm,qv,uv,mv in a['months'] if mv==0); smalln=sum(1 for mm,qv,uv,mv in a['months'] if qv<100); 
 if miss or smalln: print(n,'cost_wan',round(a['c']/10000,2),'missing_months',miss,'small_months',smalln,'n',a['n'])
print('HUAMIAN')
for n,a in rows:
 if '118D' in str(n): print(n,a)
