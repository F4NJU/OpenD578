from pathlib import Path
import html
R=Path(__file__).resolve().parents[1];out=R/'site-assets/audio';out.mkdir(exist_ok=True)
try:
 from PIL import ImageFont
 font=ImageFont.truetype('DejaVuSans.ttf',15)
 bold=ImageFont.truetype('DejaVuSans-Bold.ttf',17)
except ImportError:
 font=bold=None
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1980" viewBox="0 0 1500 1980" role="img" aria-labelledby="title desc"><title id="title">OpenD578 — audio RX, TX et réglages</title><desc id="desc">Trait vert : trajet PCM raccordé dans le banc. Bleu : commande firmware validée. Orange pointillé : trajet fonctionnel avec raccordement ou réponse encore non déterminés.</desc><defs>']
for name,color in [('ctrl','#215da8'),('pcm','#087e64'),('open','#ae6100')]:svg.append(f'<marker id="{name}" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8Z" fill="{color}"/></marker>')
svg.append('</defs><style>text{font-family:DejaVu Sans,Arial,sans-serif;fill:#183040}.title{font-size:29px;font-weight:bold}.sub{font-size:16px}.section{font-size:22px;font-weight:bold}.box{fill:white;stroke:#7894a2;stroke-width:1.6}.label{font-size:17px;font-weight:bold}.small{font-size:15px}.open{stroke:#ae6100;stroke-dasharray:8 6}.bg{fill:#f4f8fb}</style><rect width="1500" height="1980" fill="white"/>')
def text(x,y,s,cls='small',size=None):
 style=f' style="font-size:{size:.1f}px"'if size else''
 svg.append(f'<text x="{x}" y="{y}" class="{cls}"{style}>{html.escape(s)}</text>')
def box(x,y,w,title,lines,color=None):
 h=52+23*len(lines);svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" class="box"'+(f' style="stroke:{color};stroke-width:2.5"'if color else'')+'/>');text(x+14,y+28,title,'label',min(17,17*(w-28)/max(1,bold.getlength(title)if bold else len(title)*10)))
 for i,l in enumerate(lines):text(x+14,y+54+23*i,l,size=min(15,15*(w-28)/max(1,font.getlength(l)if font else len(l)*8)))
 return h
colors={'ctrl':'#215da8','pcm':'#087e64','open':'#ae6100'}
def edge(points,kind='open',label=None,lx=None,ly=None):
 svg.append(f'<polyline points="{points}" fill="none" stroke="{colors[kind]}" stroke-width="2.5" '+('stroke-dasharray="8 6" 'if kind=='open'else'')+f'marker-end="url(#{kind})"/>')
 if label:text(lx,ly,label)
def section(y,title):svg.append(f'<rect x="24" y="{y}" width="1452" height="40" rx="6" class="bg"/>');text(40,y+28,title,'section')
text(35,44,'OpenD578 — schéma bloc audio RX / TX et réglages','title');text(35,75,'Jean-Philippe (F4EGM) · PRO GD32 V1.21 · état du 9 novembre 2026','sub')
edge('40,107 110,107','pcm');text(124,113,'PCM raccordé aux bornes indiquées');edge('610,107 680,107','ctrl');text(694,113,'Commande OEM validée');edge('1040,107 1110,107','open');text(1124,113,'Raccordement / loi ouverts')
section(140,'1 · Réception FM : de l’antenne aux sorties audio')
for x,t,lines in [(40,'Antenne',['Signal VHF / UHF','Entrée RF du poste']),(330,'Préselection RF',['Filtres / commutation','Bandes VHF et UHF']),(620,'Synthèse et réception',['4 banques RF commandées','LO / FI non attribués','au seul numéro de banque']),(910,'Audio RX A / B',['Gains RF : registre 0x44','Loi en dB encore ouverte']),(1200,'U2429, 2 canaux',['IN1 → OUT1 / IN2 → OUT2','0 à −83 dB ou coupure','Sources A/B : à attribuer'])]:box(x,205,260,t,lines)
for x in [300,590,880,1170]:edge(f'{x},255 {x+30},255')
box(610,390,300,'Routage / amplificateurs',['Ordre des étages non fixé','MC34119 / YD1517 PRO','PA1517 PLUS : selon variante'])
for x,t,l in [(40,'HP du poste',['Mute commandé par PA7','1 coupe / 0 ouvre']),(1020,'HP du microphone',['Mute : banque 1 / 0x25 bit 4','1 coupe / 0 ouvre']),(1020,'Prises HP externes',['Affectation A/B et contacts','des prises : non résolus'])]:
 y=390 if t!='Prises HP externes'else 540;box(x,y,390 if x==1020 else 350,t,l)
edge('1330,326 1330,368 760,368 760,390');edge('610,445 390,445');edge('910,445 1020,445');edge('910,455 970,455 970,588 1020,588')
box(40,545,500,'Commandes de sélection OEM',['Mic Spk / Radio Spk / Both → coupures séparées','PIO 0x25 bit 7 : préférence MAIN / SUB','PIO bit 2 : porte contextuelle ; pas un sélecteur A/B'])
section(700,'2 · Émission FM : du microphone à l’antenne')
for x,t,l in [(40,'Microphone filaire',['Signal audio de la capsule','Trajet analogique terminal ouvert']),(330,'Entrée micro RF',['0x18 : sélecteur Level 1…6','Page 1 / 0x17 : MIC ajusté','Gain en dB non attribué']),(620,'Modulation FM',['0x40 : MODV1 / MODU','0x51 : champ CTCW','Filtrage / limiteur ouverts']),(910,'Chaîne TX VHF / UHF',['Consigne PA4 / DAC0','Portes PE6 et PC4','Synchronisation PD0']),(1200,'PA et antenne',['2 × AFT05MP075N','Consigne ≠ puissance mesurée','ROS : réaction non identifiée'])]:box(x,760,260,t,l)
for x in [300,590,880,1170]:edge(f'{x},815 {x+30},815')
box(40,940,430,'NAND : calibration propre au poste',['MIC +0x19 ; MODU +0x05 ; MODV1 +0x45','CTCW +0x06 ; DCSW +0x07','Copies 0x02F60000 / 0x02F80000'])
box(570,940,400,'Réglage utilisateur AnaMic',['Level 1…6 → sélecteurs 2…7','MIC ajusté : +1, −2, 0, 0, +1, +1','Application vérifiée lors du TX'])
edge('255,940 255,916 460,916 460,881','ctrl');edge('470,1000 520,1000 520,915 750,915 750,881','ctrl');edge('570,985 505,985 505,900 450,900 450,881','ctrl')
box(1040,940,420,'Tonalités / APRS TX',['PB9 : TIMER3_CH3, PWM audio','Échantillons produits par l’OEM','Point de mélange analogique non attribué']);edge('1250,940 1250,920 780,920 780,881')
section(1100,'3 · Volumes : commandes et trajet raccordé dans le banc')
for x,t,l in [(40,'Potentiomètres A / B',['PC2 ADC12 / PC5 ADC15','Acquisitions décidées par l’OEM']),(330,'GD32 : quantification',['0…4095 → niveaux 0…32','Tables OEM : code d’atténuation','Niveau 0 : coupure']),(620,'Bus série U2429',['PA13 DATA / PA14 CLOCK','11 bits, D0 canal / D1 commun','Latch de fin de mot']),(910,'Transfert U2429',['Gain = 10^(−atténuation/20)','PCM varie à chaque latch','Aucune loi RF en dB inventée']),(1200,'OUT1 / OUT2 du modèle',['Écoute et export WAV','Ports du composant uniquement','Pas encore des sorties HP'])]:box(x,1160,260,t,l,'#087e64'if x>=910 else None)
for x in [300,590,880]:edge(f'{x},1215 {x+30},1215','ctrl')
edge('1170,1215 1200,1215','pcm');text(910,1330,'Source WAV explicitement raccordée à IN1 / IN2. Temps virtuel du banc.')
section(1380,'4 · Codec / SCT et acquisition GD32 : chemins distincts')
box(40,1440,430,'GD32 → HPI → SCT3258',['Demandes de commande et acquittements','Paramètres codec / coefficients / gains','L’exécution DSP complète reste ouverte'])
box(570,1440,410,'TLV320AIC3204',['PGA micro : demi-dB, registres page 1','Gains numériques ADC / DAC','Drivers HPL/HPR/LOL/LOR, mutes','AGC : champs connus, dynamique ouverte'])
box(1050,1440,410,'Corrections SCT documentées',['3 sections IIR RX + 3 sections TX, 24 kHz','Coefficients signés Q14 ; Q11/Q12 gains','Ordre et route FM effectifs à établir'])
edge('470,1500 570,1500','ctrl');edge('470,1520 510,1520 510,1428 1255,1428 1255,1440','ctrl')
text(40,1640,'Ces commandes ne prouvent pas que toute la voix FM traverse le GD32 en PCM. Les routes I²S / RF / codec ne sont pas refermées ici.','sub')
for x,t,l in [(40,'WAV de test RX',['Codes ADC12 explicitement choisis','Polarisation / amplitude de scénario']),(400,'PC0 / ADC0_IN10',['Acquisition audio RX / signalisation','Source temporelle, sans file de reprise']),(760,'DMA configuré par le CPU',['Destination SRAM et rangs par l’OEM','Pas d’écriture directe d’un buffer OEM']),(1120,'Décodeurs du programme',['Échantillons réellement acquis','Capture JSON exportable'])]:box(x,1690,310,t,l,'#087e64')
for x in [350,710,1070]:edge(f'{x},1740 {x+50},1740','pcm')
text(40,1850,'Liaisons de commande établies par firmware retenues validées. Pointillés : information manquante rendue visible, pas remplacée par un mixeur fictif.','sub')
text(40,1880,'Les HP externes, la loi des gains RF, la réponse des filtres / limiteurs et le ROS restent à caractériser. DMR différé.','sub')
text(40,1930,'Références : tableau IO N1–N14 · audio OEM V0.13 · calibrations V0.12 · fréquences OEM 0x38/0x39 · sources et tests du dépôt.','small')
svg.append('</svg>');(out/'schema_audio_rx_tx.svg').write_text('\n'.join(svg))
(out/'index.html').write_text('''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>OpenD578 — schéma audio RX/TX</title><style>body{font:16px system-ui;margin:24px;color:#183040}img{width:100%;min-width:900px}.scroll{overflow:auto}a{margin-right:18px}button{padding:8px}p{max-width:1100px}</style><nav><a href="../index.html">Vue éclatée</a><a href="../simulator/index.html">Simulateur</a><a href="../io/index.html">Tableau IO</a><a href="../doc/docs/peripherals/09_SCHEMA_AUDIO_RX_TX_ET_RACCORDEMENTS.html">Explication et réglages</a><a href="schema_audio_rx_tx.svg" download>Télécharger le SVG</a></nav><h1>Audio RX / TX : trajets et commandes</h1><p>Le schéma distingue le signal audio, les commandes OEM et les raccordements ouverts. L’essai U2429 traite les échantillons aux bornes du composant ; il ne certifie pas toute la chaîne voix du poste.</p><label>Zoom <input type="range" min="60" max="180" value="100" oninput="document.querySelector('img').style.width=this.value+'%'"> </label><div class="scroll"><img src="schema_audio_rx_tx.svg" alt="Schéma audio RX, TX, volumes et codec, avec raccordements ouverts en pointillés"></div></html>''')
print(out/'schema_audio_rx_tx.svg')
