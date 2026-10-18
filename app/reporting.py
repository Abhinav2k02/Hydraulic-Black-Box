"""Printable server-recomputed evidence. No unverified browser diagnosis is accepted."""
from io import BytesIO
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
FONT_DIR=Path(__file__).parent/'fonts'
for name,file in [('AppSans','DejaVuSans.ttf'),('AppSans-Bold','DejaVuSans-Bold.ttf'),('AppSans-Oblique','DejaVuSans.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONT_DIR/file)))
pdfmetrics.registerFontFamily('AppSans',normal='AppSans',bold='AppSans-Bold',italic='AppSans-Oblique',boldItalic='AppSans-Bold')
from datetime import datetime, timezone
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.pagesizes import A4


def render_report(report, draft, engineer='', notes=''):
    out=BytesIO();styles=getSampleStyleSheet()
    for style in styles.byName.values():
        if hasattr(style,'fontName'):style.fontName='AppSans-Bold' if 'Bold' in style.fontName else 'AppSans'
    styles['BodyText'].fontSize=9.5
    styles['Heading2'].fontSize=13
    styles['Heading3'].fontSize=10.5
    styles.add(ParagraphStyle(name='SmallNote',fontName='AppSans',fontSize=9,leading=13,textColor=colors.HexColor('#526574')))
    styles['BodyText'].leading=15
    def clean(v):
        return escape(str(v).replace('₹','INR ').replace('→',' to ').replace('—','-').replace('–','-').replace('’',"'").replace('−','-'))
    def p(v,style='BodyText'):return Paragraph(clean(v).replace('\n','<br/>'),styles[style])
    story=[p('HYDRAULIC BLACK BOX','Title'),p('Inspection report - draft for human review','Heading2'),
           p('Generated '+datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),'SmallNote'),
           p('Evidence: '+('UCI recording '+str(report['cycle_id']) if report['cycle_id'] else 'User-uploaded measurements')),
           p('Screening: '+report['label_name'],'Heading2'),p(report['quality']['title']),
           p(report['scope'],'SmallNote')]
    story.append(p('1. What needs attention','Heading2'))
    for reason in report['quality']['reasons']:story.append(p('- '+reason))
    story.append(p(report['quality']['limitation'],'SmallNote'))
    story.append(p('2. Measured evidence','Heading2'))
    rows=[[p(v,'SmallNote') for v in ['Sensor','Cycle mean','No-leak training mean']]]
    for e in report['evidence'][:6]:
        rows.append([p(e['sensor']+' - '+e['quantity'],'SmallNote'),p(str(e['mean'])+' '+e['unit'],'SmallNote'),p(str(e['baseline'])+' '+e['unit'],'SmallNote')])
    table=Table(rows,colWidths=[205,120,150],repeatRows=1,hAlign='LEFT')
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5f1eb')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#d5dfda'))]))
    story.extend([table,p('Broad training comparisons are descriptive, not proof of causation.','SmallNote')])
    story.append(p('3. Verification checklist','Heading2'))
    for i,c in enumerate(report['verification']['checks'],1):
        story.append(KeepTogether([p(f'{i}. '+c['title'],'Heading3'),p(c['why']),p('Needed: '+c['needed']),p('Decision: '+c['decision'])]))
    story.append(p('4. Reference guidance','Heading2'))
    for ref in report['verification']['manual_references']:
        story.extend([p(ref['id']+' | '+ref['title'],'Heading3'),p(ref['section']),p(ref['summary']),p(ref['applicability'],'SmallNote'),
                      Paragraph('<link href="'+escape(ref['url'],{'"':'&quot;'})+'" color="#167054">Open source manual</link>',styles['BodyText'])])
    story.append(p('5. Optional cost scenario','Heading2'))
    cost=draft.get('illustrative_cost')
    if cost:
        inp=cost['inputs']
        story.extend([
            p(f"Setting {cost['setting_id']} | Tariff INR {inp['tariff_inr_kwh']:,.2f}/kWh | {inp['hours_per_day']} hours/day | {inp['days_per_year']} days/year",'SmallNote'),
            p(f"Measured power difference: {cost['measured_extra_power_w']:,.2f} W. Illustrative annual energy difference: {cost['annual_extra_energy_kwh']:,.2f} kWh."),
            p(f"Illustrative annual extra cost: INR {cost['annual_extra_cost_inr']:,.2f}; monthly average: INR {cost['average_monthly_extra_cost_inr']:,.2f}."),
            p('Scenario: '+('Severe' if inp['leakage']==2 else 'Weak')+' leakage versus no leakage. This grouping is separate from the current prediction.','SmallNote'),
            p(cost['formula'],'SmallNote'),p(cost['limitations'],'SmallNote')])
        for assumption in cost['assumptions']:story.append(p('- '+assumption,'SmallNote'))
    else:story.append(p('Not calculated. Explicit tariff, schedule and comparison setting are required.'))
    story.append(p('6. Engineer review','Heading2'))
    story.extend([p('Engineer: '+(engineer or 'Not supplied')),p('Notes: '+(notes or 'No inspection findings entered.')),
                  p('Human-entered name and notes are not authenticated approval. No maintenance is sent or scheduled.','SmallNote'),
                  p('This PDF uses server-recomputed measurements and deterministic checklists. It does not include an AI narrative or certify the diagnosis.','SmallNote'),
                  p('Dataset: UCI Condition monitoring of hydraulic systems (2015), CC BY 4.0, DOI 10.24432/C5CW21.','SmallNote')])
    def footer(canvas,doc):
        canvas.setFont('AppSans',8);canvas.setFillColor(colors.HexColor('#526574'))
        canvas.drawString(42,25,'Research prototype | Not a confirmed diagnosis');canvas.drawRightString(A4[0]-42,25,str(doc.page))
    SimpleDocTemplate(out,pagesize=A4,rightMargin=42,leftMargin=42,topMargin=36,bottomMargin=42,title='Hydraulic inspection report').build(story,onFirstPage=footer,onLaterPages=footer)
    return out.getvalue()
