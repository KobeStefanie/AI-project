# -*- coding: utf-8 -*-
import os, pickle
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION

ROOT = r'D:\AI-椤圭洰\12-鎴愭湰鎺у埗'
DATA = os.path.join(ROOT, 'months_data_correct.pkl')
OUT = os.path.join(ROOT, '01-浜や粯鐗╁綊妗?, '2026-09', '缁囬€犺溅闂存垚鏈綋绯诲缓璁綺浼樺寲鐗坃202609.pptx')
with open(DATA, 'rb') as f:
    months = pickle.load(f)
MONTHS = ['4鏈?,'5鏈?,'6鏈?,'7鏈?,'8鏈?]
all_rows = [x for m in MONTHS for x in months[m]]

def sums(rows):
    return {
        'qty': sum(x['瀹炴敹鏁伴噺'] for x in rows),
        'cost': sum(x['瀹為檯鎴愭湰鍚堣'] for x in rows),
        'mat': sum(x['鍘熸潗鏂欓噾棰?] for x in rows),
        'lab': sum(x['浜哄伐灏忚'] for x in rows),
        'mfg': sum(x['鍒堕€犺垂鐢ㄥ皬璁?] for x in rows),
    }
monthly = {m: sums(months[m]) for m in MONTHS}
valid = {m: [x for x in months[m] if x['鍘熸潗鏂欓噾棰?] > 0 and x['瀹炴敹鏁伴噺'] >= 100] for m in ['7鏈?,'8鏈?]}
valid_sum = {m: sums(valid[m]) for m in valid}
missing = sum(x['鍘熸潗鏂欓噾棰?] == 0 for x in all_rows)
small = sum(x['瀹炴敹鏁伴噺'] < 100 for x in all_rows)

# Palette
NAVY = RGBColor(20, 38, 63)
INK = RGBColor(35, 45, 56)
MUTED = RGBColor(103, 116, 128)
TEAL = RGBColor(19, 139, 143)
CORAL = RGBColor(222, 91, 75)
GOLD = RGBColor(224, 164, 58)
CREAM = RGBColor(247, 245, 239)
WHITE = RGBColor(255, 255, 255)
LINE = RGBColor(220, 225, 228)
GREEN = RGBColor(69, 145, 95)
FONT = 'Microsoft YaHei'

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]

def fill_bg(slide, color=CREAM):
    bg = slide.background.fill
    bg.solid(); bg.fore_color.rgb = color

def rect(slide, x, y, w, h, fill, line=None, radius=False):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid(); shp.fill.fore_color.rgb = fill
    shp.line.color.rgb = line or fill
    if radius:
        shp.adjustments[0] = 0.08
    return shp

def txt(slide, text, x, y, w, h, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT, font=FONT, margin=0.06, valign=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame; tf.clear(); tf.word_wrap = True; tf.margin_left = Inches(margin); tf.margin_right = Inches(margin); tf.margin_top = Inches(margin); tf.margin_bottom = Inches(margin); tf.vertical_anchor = valign
    p = tf.paragraphs[0]; p.text = text; p.alignment = align
    p.font.name = font; p.font.size = Pt(size); p.font.bold = bold; p.font.color.rgb = color
    return box

def title(slide, kicker, heading, note=None):
    txt(slide, kicker.upper(), 0.62, 0.35, 2.6, 0.28, 10, TEAL, True)
    txt(slide, heading, 0.62, 0.64, 11.8, 0.58, 27, NAVY, True)
    if note: txt(slide, note, 0.64, 1.2, 11.8, 0.35, 11, MUTED)
    rect(slide, 0.62, 1.55, 12.08, 0.02, LINE)

def footer(slide, text='鏁版嵁鏉ユ簮锛氭垚鏈牳绠楁眹鎬昏〃锛?-8鏈堬級锝滈噾棰濆崟浣嶏細鍏冿紝姣斾緥鎸夊疄闄呮垚鏈绠?):
    txt(slide, text, 0.62, 7.18, 12.0, 0.18, 8.5, MUTED)

def kpi(slide, x, y, w, label, value, sub='', accent=TEAL):
    rect(slide, x, y, w, 1.12, WHITE, LINE, True)
    rect(slide, x, y, 0.08, 1.12, accent, accent)
    txt(slide, label, x+0.22, y+0.16, w-0.32, 0.22, 10.5, MUTED, True)
    txt(slide, value, x+0.22, y+0.42, w-0.32, 0.38, 24, NAVY, True)
    if sub: txt(slide, sub, x+0.22, y+0.84, w-0.32, 0.18, 9.5, MUTED)

def bullet(slide, text, x, y, w, color=INK, size=14, accent=TEAL):
    rect(slide, x, y+0.10, 0.10, 0.10, accent, accent, True)
    txt(slide, text, x+0.22, y, w-0.22, 0.34, size, color)

def add_bar_chart(slide, x, y, w, h, categories, series, colors):
    data = CategoryChartData(); data.categories = categories
    for name, vals in series: data.add_series(name, vals)
    chart = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), data).chart
    chart.has_legend = True; chart.legend.position = XL_LEGEND_POSITION.BOTTOM; chart.legend.include_in_layout = False
    chart.value_axis.has_major_gridlines = True; chart.value_axis.major_gridlines.format.line.color.rgb = LINE
    chart.category_axis.tick_labels.font.size = Pt(10); chart.value_axis.tick_labels.font.size = Pt(9)
    chart.chart_title.has_text_frame = False
    for i, s in enumerate(chart.series):
        s.format.fill.solid(); s.format.fill.fore_color.rgb = colors[i]; s.format.line.color.rgb = colors[i]
    return chart

def add_column_chart(slide, x, y, w, h, categories, series, colors):
    data = CategoryChartData(); data.categories = categories
    for name, vals in series: data.add_series(name, vals)
    chart = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), data).chart
    chart.has_legend = True; chart.legend.position = XL_LEGEND_POSITION.BOTTOM; chart.legend.include_in_layout = False
    chart.value_axis.has_major_gridlines = True; chart.value_axis.major_gridlines.format.line.color.rgb = LINE
    chart.category_axis.tick_labels.font.size = Pt(10); chart.value_axis.tick_labels.font.size = Pt(9)
    for i, s in enumerate(chart.series):
        s.format.fill.solid(); s.format.fill.fore_color.rgb = colors[i]; s.format.line.color.rgb = colors[i]
    return chart

# 1. Executive cover
s = prs.slides.add_slide(blank); fill_bg(s, NAVY)
rect(s, 0, 0, 13.333, 7.5, NAVY)
rect(s, 0, 0, 0.24, 7.5, CORAL)
txt(s, '缁囬€犺溅闂?, 0.85, 1.15, 3.0, 0.35, 15, RGBColor(152, 211, 209), True)
txt(s, '鎴愭湰绠＄悊浣撶郴寤鸿', 0.82, 1.62, 8.8, 0.78, 40, WHITE, True)
txt(s, '4-8鏈堢涓€鐗堟暟鎹鐩?, 0.86, 2.58, 7.4, 0.48, 24, RGBColor(222, 229, 234), False)
rect(s, 0.86, 3.42, 5.2, 0.04, TEAL)
txt(s, '鍏堟妸鏁版嵁璇存竻妤氾紝鍐嶆妸鎴愭湰绠¤捣鏉?, 0.86, 3.75, 7.3, 0.42, 19, RGBColor(236, 240, 241), True)
rect(s, 8.95, 1.22, 3.45, 4.8, RGBColor(30, 57, 83), RGBColor(54, 82, 107), True)
txt(s, '鏈姹囨姤鍙洖绛斾笁涓棶棰?, 9.35, 1.65, 2.7, 0.45, 16, WHITE, True)
bullet(s, '闂鏈夊澶э紵', 9.35, 2.45, 2.5, RGBColor(229,239,240), 15, CORAL)
bullet(s, '鍝簺鏁版嵁鍙互鐩镐俊锛?, 9.35, 3.2, 2.7, RGBColor(229,239,240), 15, GOLD)
bullet(s, '9-11鏈堝厛鍋氫粈涔堬紵', 9.35, 3.95, 2.7, RGBColor(229,239,240), 15, TEAL)
txt(s, '璐㈠姟閮綔2026骞?鏈?, 0.86, 6.78, 3.0, 0.22, 10, RGBColor(177, 193, 202))

# 2. Executive conclusion
s = prs.slides.add_slide(blank); fill_bg(s); title(s, '01锝滃厛鐪嬬粨璁?, '绗竴鐗堟暟鎹凡缁忚冻澶熻鏄庯細鍏堟不鐞嗘暟鎹紝鍐嶈皥绮剧粏鍖栨垚鏈?, '4-8鏈堝叡168鏉¤褰曪紝褰撳墠鏈€閲嶈鐨勭鐞嗗姩浣滄槸鎶婇鏂欏拰鐩樼偣鍙樻垚鍙拷婧祦绋嬨€?)
kpi(s, 0.62, 1.88, 2.8, '鏍锋湰璁板綍', '168 鏉?, '4-8鏈堝叏閮ㄨ褰?, TEAL)
kpi(s, 3.62, 1.88, 2.8, '鍘熸潗鏂欑己澶?, '69 鏉?, '鍗?41.1%锛屼笉鑳界洿鎺ョ敤浜庢垚鏈垽鏂?, CORAL)
kpi(s, 6.62, 1.88, 2.8, '灏忔壒閲忚褰?, '105 鏉?, '浜ч噺 <100KG锛屽崰 62.5%', GOLD)
kpi(s, 9.62, 1.88, 2.8, '瀹屾暣鍙瘮鏍锋湰', '7-8鏈?, '鍓旈櫎缂烘枡涓庡皬鎵归噺鍚庡啀姣旇緝', GREEN)
rect(s, 0.62, 3.35, 12.08, 2.65, WHITE, LINE, True)
txt(s, '绠＄悊鍒ゆ柇', 0.92, 3.68, 1.4, 0.28, 12, TEAL, True)
txt(s, '褰撳墠涓嶈兘鐢ㄥ叏閲忔暟鎹洖绛斺€滃摢涓搧绉嶆渶璧氶挶鈥濄€?, 0.92, 4.05, 6.8, 0.42, 22, NAVY, True)
bullet(s, '鍙互纭锛氬師鏉愭枡鏄垚鏈帶鍒剁殑绗竴鎶撴墜锛屽繀椤荤粦瀹氳鍗曞拰鐩樼偣銆?, 0.94, 4.72, 10.7, INK, 14, TEAL)
bullet(s, '鍙互鎺ㄨ繘锛?鏈堝厛鎶婃暟鎹畬鏁寸巼鍜岄鏂欐祦绋嬪仛瀹烇紝10鏈堝啀鍋氬伐搴忕骇鍒嗘憡銆?, 0.94, 5.16, 10.7, INK, 14, CORAL)
footer(s)

# 3. Data scope and quality
s = prs.slides.add_slide(blank); fill_bg(s); title(s, '02锝滄暟鎹竟鐣?, '鍏堟妸鈥滆兘涓嶈兘姣斺€濊娓呮锛岄伩鍏嶇敤缂哄け鏁版嵁鍋氱粨璁?)
# left funnel
rect(s, 0.72, 1.92, 5.0, 4.55, WHITE, LINE, True)
txt(s, '168鏉¤褰曞浣曞垎灞?, 1.02, 2.2, 3.8, 0.3, 15, NAVY, True)
rect(s, 1.05, 2.83, 4.3, 0.66, TEAL, TEAL, True); txt(s, '鍏ㄩ儴璁板綍 168 鏉?, 1.22, 3.02, 3.9, 0.25, 18, WHITE, True, PP_ALIGN.CENTER)
rect(s, 1.42, 3.75, 3.56, 0.66, CORAL, CORAL, True); txt(s, '鍘熸潗鏂欓噾棰濅负 0锛?9 鏉?, 1.52, 3.94, 3.35, 0.25, 15, WHITE, True, PP_ALIGN.CENTER)
rect(s, 1.78, 4.67, 2.84, 0.66, GOLD, GOLD, True); txt(s, '浜ч噺 <100KG锛?05 鏉?, 1.86, 4.86, 2.7, 0.25, 14, WHITE, True, PP_ALIGN.CENTER)
rect(s, 2.10, 5.59, 2.20, 0.52, GREEN, GREEN, True); txt(s, '鍙瘮鏍锋湰锛?-8鏈?, 2.18, 5.73, 2.05, 0.20, 12, WHITE, True, PP_ALIGN.CENTER)
# right notes
rect(s, 6.02, 1.92, 6.68, 4.55, RGBColor(240,247,246), RGBColor(197,225,222), True)
txt(s, '杩欐剰鍛崇潃浠€涔?, 6.38, 2.25, 3.0, 0.3, 15, NAVY, True)
bullet(s, '4-6鏈堟病鏈夋湡鍒濈洏鐐癸紝鍘熸潗鏂欐暟鎹笉瀹屾暣銆?, 6.38, 2.95, 5.8, INK, 14, CORAL)
bullet(s, '鍏ㄩ噺鏁版嵁閫傚悎鎵剧鐞嗛棶棰橈紝涓嶉€傚悎鐩存帴鍋氬搧绉嶇泩鍒╂帓鍚嶃€?, 6.38, 3.55, 5.8, INK, 14, GOLD)
bullet(s, '7-8鏈堝墧闄ょ己鏂欎笌灏忔壒閲忓悗锛屾墠浣滀负鈥滅浉瀵瑰彲姣斺€濈殑瓒嬪娍鍙傝€冦€?, 6.38, 4.15, 5.8, INK, 14, TEAL)
bullet(s, '鍚庣画姣忔湀鍥哄畾杈撳嚭锛氬叏閮ㄦ牱鏈€佸彲姣旀牱鏈€佸墧闄ゅ師鍥犱笁寮犳竻鍗曘€?, 6.38, 4.75, 5.8, INK, 14, GREEN)
footer(s, '鏁版嵁鍙ｅ緞锛氱己鏂?= 鍘熸潗鏂欓噾棰濅负0锛涘皬鎵归噺 = 瀹炴敹鏁伴噺<100KG锛涗袱绫昏褰曞彲閲嶅彔銆?)

# 4. Cost composition
s = prs.slides.add_slide(blank); fill_bg(s); title(s, '03锝滄垚鏈粨鏋?, '鍘熸潗鏂欏崰姣旇繙楂樹簬鍙傝€冨尯闂达紝鎴愭湰鏀瑰杽瑕佷粠鈥滄枡鈥濆紑濮?, '琛屼笟鍙傝€冧粎浣滄柟鍚戞€у熀鍑嗭紝褰撳墠鏁版嵁浠嶅彈鐩樼偣鍜岄鏂欏畬鏁存€у奖鍝嶃€?)
# chart on left
cats = MONTHS
mat_pct = [monthly[m]['mat']/monthly[m]['cost']*100 if monthly[m]['cost'] else 0 for m in MONTHS]
lab_pct = [monthly[m]['lab']/monthly[m]['cost']*100 if monthly[m]['cost'] else 0 for m in MONTHS]
mfg_pct = [monthly[m]['mfg']/monthly[m]['cost']*100 if monthly[m]['cost'] else 0 for m in MONTHS]
add_column_chart(s, 0.75, 1.95, 7.2, 4.65, cats, [('鍘熸潗鏂?, mat_pct), ('浜哄伐', lab_pct), ('鍒堕€犺垂鐢?, mfg_pct)], [CORAL, TEAL, GOLD])
rect(s, 8.35, 1.95, 4.35, 4.65, WHITE, LINE, True)
txt(s, '璇诲浘缁撹', 8.7, 2.27, 2.5, 0.3, 15, NAVY, True)
txt(s, '89%-94%', 8.7, 2.85, 3.2, 0.62, 34, CORAL, True)
txt(s, '鍘熸潗鏂欐垚鏈崰姣旓紙4-8鏈堬級', 8.72, 3.48, 3.4, 0.3, 11, MUTED)
bullet(s, '鍘熺罕閲囪喘浠枫€佺敤閲忓拰缁囨崯鏄涓€浼樺厛绾с€?, 8.7, 4.1, 3.55, INK, 13, CORAL)
bullet(s, '浜哄伐鍜屽埗閫犺垂鐢ㄥ崰姣斾綆锛屽厛涓嶈鐢ㄥ畠浠В閲婂叏閮ㄦ尝鍔ㄣ€?, 8.7, 4.78, 3.55, INK, 13, TEAL)
footer(s)

# 5. Comparable 7-8
s = prs.slides.add_slide(blank); fill_bg(s); title(s, '04锝滃彲姣旀牱鏈?, '7-8鏈堢殑鏈夋晥鏍锋湰鏄剧ず锛氬崟浣嶆垚鏈笅闄嶏紝浣嗕笉鑳界畝鍗曞綊鍥犱簬绠＄悊鏀瑰杽', '鏈夋晥鏍锋湰瀹氫箟锛氬師鏉愭枡閲戦>0 涓斾骇閲忊墺100KG锛涚敤浜庤秼鍔胯瀵燂紝涓嶇瓑浜庢渶缁堝埄娑﹀彛寰勩€?)
# chart
cats2=['7鏈?,'8鏈?]; unit=[valid_sum[m]['cost']/valid_sum[m]['qty'] for m in cats2]
add_column_chart(s, 0.78, 1.95, 5.1, 4.55, cats2, [('骞冲潎鍗曚綅鎴愭湰锛堝厓/KG锛?, unit)], [TEAL])
for i,m in enumerate(cats2):
    x=6.2+i*3.05
    d=valid_sum[m]; total=d['cost'];
    rect(s,x,2.0,2.7,3.95,WHITE,LINE,True)
    txt(s,m,x+0.25,2.28,2.2,0.3,18,NAVY,True)
    txt(s,f'{len(valid[m])} 涓湁鏁堝搧绉?,x+0.25,2.72,2.2,0.25,10,MUTED)
    txt(s,f'{d["cost"]/10000:.1f} 涓囧厓',x+0.25,3.18,2.2,0.45,23,NAVY,True)
    txt(s,f'{d["qty"]/1000:.1f} 鍚?,x+0.25,3.72,2.2,0.25,11,MUTED)
    txt(s,f'{d["cost"]/d["qty"]:.2f} 鍏?KG',x+0.25,4.25,2.2,0.34,16,TEAL,True)
    txt(s,f'鍘熸潗鏂欏崰姣?{d["mat"]/total*100:.1f}%',x+0.25,4.82,2.2,0.24,10,MUTED)
    txt(s,f'浜哄伐+鍒堕€?{((d["lab"]+d["mfg"])/total*100):.1f}%',x+0.25,5.20,2.2,0.24,10,MUTED)
rect(s, 0.78, 6.68, 11.9, 0.34, RGBColor(255,246,229), RGBColor(242,218,169), True)
txt(s, '鎻愮ず锛?鏈堝埌8鏈堟垚鏈笅闄嶅悓鏃朵即闅忎骇閲忓拰鍝佺缁撴瀯鍙樺寲锛屼笅涓€姝ュ繀椤诲垎瑙ｂ€滀环鏍笺€佺敤閲忋€佷骇鍝佺粨鏋勨€濅笁椤瑰奖鍝嶃€?, 1.0, 6.76, 11.45, 0.18, 10.5, INK, True)
footer(s)

# 6. Action plan
s = prs.slides.add_slide(blank); fill_bg(s); title(s, '05锝滆鍔ㄨ鍒?, '9-11鏈堟寜鏈堝彧鍋氫竴浠跺叧閿簨锛氬厛瀹屾暣锛屽啀绮剧粏锛屾渶鍚庨璀?)
# timeline
rect(s, 1.02, 3.3, 11.0, 0.07, LINE)
steps=[('9月','把数据补齐','按订单领料；每日核对ERP出库；次品单独登记',CORAL),('10月','把成本算准','工序采集器；按品种分摊人工；标准用量复盘',TEAL),('11月','把异常提前发现','变动率>10%预警；月度成本会；看板试运行',GOLD)]
for i,(month,head,body,col) in enumerate(steps):
    x=1.05+i*3.72
    rect(s,x,2.68,0.48,0.48,col,col,True); txt(s,str(i+1),x,2.78,0.48,0.22,14,WHITE,True,PP_ALIGN.CENTER)
    rect(s,x+0.58,2.55,2.55,2.0,WHITE,LINE,True)
    txt(s,month,x+0.82,2.82,1.3,0.24,13,col,True)
    txt(s,head,x+0.82,3.18,2.0,0.3,16,NAVY,True)
    txt(s,body,x+0.82,3.68,1.95,0.76,12,INK)
# bottom metrics
kpi(s, 1.05, 5.35, 3.25, '9鏈堥獙鏀?, '瀹屾暣鐜?鈮?0%', '鎸夎鍗曢鏂欒鐩栦富鍔涘搧绉?, CORAL)
kpi(s, 4.55, 5.35, 3.25, '10鏈堥獙鏀?, '鎶ュ憡 T+2', '鎴愭湰鍒嗘憡瑙勫垯鍙鏍?, TEAL)
kpi(s, 8.05, 5.35, 3.25, '11鏈堥獙鏀?, '寮傚父鍙璀?, '鍙樺姩鐜?10%鑷姩杩涘叆娓呭崟', GOLD)
footer(s)

# 7. Decision asks
s = prs.slides.add_slide(blank); fill_bg(s, NAVY)
txt(s, '06锝滈渶瑕佺鐞嗗眰纭', 0.78, 0.62, 4.0, 0.3, 12, RGBColor(150,219,216), True)
txt(s, '鎶婃垚鏈鐞嗕粠鈥滀簨鍚庤В閲娾€濇帹杩涘埌鈥滅幇鍦哄彲鎵ц鈥?, 0.78, 1.12, 10.8, 0.62, 29, WHITE, True)
rect(s, 0.78, 2.1, 11.8, 0.03, RGBColor(74, 112, 137))
asks=[('01','鎸夎鍗曢鏂?,'纭鐢熶骇閮ㄩ厤鍚堬紝9鏈堝厛瑕嗙洊涓诲姏鍝佺銆?,CORAL),('02','娆″搧鐙珛鐧昏','纭BC绾ф鍝佸崟鐙叆搴撱€佸崟鐙彴璐︺€?,GOLD),('03','鏈堝害鎴愭湰浼?,'纭姣忔湀鍏宠处鍚庡浐瀹氬彫寮€锛屾寜鈥滃紓甯?鍘熷洜-鍔ㄤ綔鈥濋棴鐜€?,TEAL)]
for i,(num,head,body,col) in enumerate(asks):
    y=2.62+i*1.15
    rect(s,0.82,y,0.55,0.55,col,col,True); txt(s,num,0.82,y+0.14,0.55,0.20,13,WHITE,True,PP_ALIGN.CENTER)
    txt(s,head,1.65,y+0.02,3.0,0.28,18,WHITE,True)
    txt(s,body,1.65,y+0.38,9.9,0.3,13,RGBColor(218,229,235))
rect(s,0.82,6.25,11.65,0.58,RGBColor(30,57,83),RGBColor(74,112,137),True)
txt(s, '鏈増鏁版嵁鐨勪环鍊硷細鎶婇棶棰樿竟鐣岃娓呮锛屾妸涓嬩竴姝ュ姩浣滃畾涓嬫潵銆?, 1.08, 6.43, 11.1, 0.22, 15, RGBColor(237,243,245), True, PP_ALIGN.CENTER)
txt(s, '璐㈠姟閮綔2026骞?鏈?, 0.82, 7.12, 3.0, 0.18, 9, RGBColor(153,176,188))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
prs.save(OUT)
print(OUT)
