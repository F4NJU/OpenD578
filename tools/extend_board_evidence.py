#!/usr/bin/env python3
"""One-time, idempotent addition of RTC/GNSS and RF evidence nodes to models."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
BAT='docs/hardware/SAUVEGARDE_RTC_GPS_XH414HG.md'
RF='docs/hardware/ETAGES_RF_PROTECTION_FI.md'
PIN='docs/evidence/INDEX.md'

def put_node(m,n):
 if n['id'] not in {x['id'] for x in m['nodes']}:m['nodes'].append(n)

def put_edge(m,source,target,label,bus,status,docs,details,pins=None,id=None):
 id=id or (source+'-'+target)
 if id in {x['id'] for x in m['edges']}:return
 m['edges'].append({'id':id,'source':source,'target':target,'label':label,'bus':bus,'status':status,'pins':pins or [],'details':details,'docs':docs})

def node(id,label,group,x,y,subtitle,desc,conf,docs):return dict(id=id,label=label,group=group,x=x,y=y,w=260,h=74,subtitle=subtitle,description=desc,confidence=conf,docs=docs)

p=ROOT/'hardware/models/d578uv-pro-gd32-v121.json'
m=json.loads(p.read_text(encoding='utf8'))
put_node(m,node('backup_rtc','Sauvegarde RTC / XH414HG ?', 'logique',345,1130,'Face arriere PCB CPU, cote nappe','Etude D578 historique: maintien RTC par condensateur de sauvegarde XH414HG 0,08 F/3,3 V max. Observation utilisateur de composants de sauvegarde sur PCB CPU, ref exacte et liaison VBAT non mesurees.', 'partial',[BAT,PIN]))
put_node(m,node('backup_gps','Sauvegarde GPS hot start ?', 'peripheriques',665,1550,'Face avant PCB CPU, entre volumes','Deuxieme sauvegarde externe historique affectee au GNSS. Presence precise, type de la piece et continute VBAT GPS PRO restent a verifier.', 'partial',[BAT,'docs/peripherals/02_GPS_ATGM336H_UART_NMEA_RAM_PARAMETRES.md']))
put_node(m,node('protection_supply','Protection alimentation', 'logique',345,1250,'Relais et diode, d apres VK7ZJA','La documentation historique D578 decrit relais et diode de protection contre inversion; leur implantation sur la revision GD32 et le rail regulateur restent inconnus.', 'candidate',[RF,'docs/hardware/ALIMENTATION_L7805CV.md']))
put_node(m,node('varicaps_rx','Filtres RX varicaps', 'radio',985,1590,'VHF / UHF, filtres accordables','Quatre etages accordables par varicaps decrits dans les D578 historiques. Affectations DAC et commutations de ce PCB non etablies.', 'candidate',[RF,'docs/hardware/BH2226_H2226_DAC_RF.md']))
put_node(m,node('fi_spare','FI supplementaire non peuplee ?', 'radio',985,1700,'Empreintes sur anciens D578','Empreinte de circuit IF supplementaire documentee sur une revision historique; pas constatee sur le PCB PRO de ce projet.', 'candidate',[RF]))
put_edge(m,'backup_rtc','mcu','RTC -> VBAT GD32 (a verifier)','Alimentation de sauvegarde','hypothesis',[BAT,PIN], 'La datasheet confirme VBAT pin 6 du GD32. VK7ZJA attribue la sauvegarde arriere au RTC. La piste reelle sur notre carte est inconnue.',[{'from_pin':'Sortie composant backup RTC, non relevee','to_pin':'VBAT pin 6, GD32 (CANDIDAT)','status':'hypothesis'}])
put_edge(m,'backup_gps','gps','Hot start GPS -> VBAT GNSS (a verifier)','Alimentation de sauvegarde','hypothesis',[BAT,'docs/peripherals/02_GPS_ATGM336H_UART_NMEA_RAM_PARAMETRES.md'],'La sauvegarde GPS est signalee entre les volumes sur un D578 historique. Pin VBAT du suffixe GPS monte et continuite a relever.')
put_edge(m,'power','backup_rtc','Charge reserve RTC a verifier','Alimentation','hypothesis',[BAT],'L etude historique decrit une recharge sous alimentation externe meme poste logiquement eteint. Aucun schema de charge releve ici.')
put_edge(m,'power','backup_gps','Charge reserve GPS a verifier','Alimentation','hypothesis',[BAT],'L etude historique decrit recharge sous alimentation externe, sans mesurer les rails precis de notre revision.')
put_edge(m,'power','protection_supply','Entree 13,8 V / protection','Alimentation','unknown',[RF],'Position de relais et diode dans notre etagement a suivre hors tension; la documentation externe n etablit pas cette piste sur notre version.')
put_edge(m,'protection_supply','l7805','Protection -> regulateur 5 V ?','Alimentation','unknown',[RF,'docs/hardware/ALIMENTATION_L7805CV.md'],'Aucune continuite connue entre la protection, le transistor de Power et le L7805CV.')
put_edge(m,'bh2226','varicaps_rx','DAC -> varicaps : hypothese','Tensions analogiques','hypothesis',[RF,'docs/hardware/BH2226_H2226_DAC_RF.md'],'Un BH2226 produit des tensions de commande et les D578 historiques emploient des varicaps. Aucune DAx n a ete reliee a un varicap.')
put_edge(m,'rf','varicaps_rx','Filtres RF accordables','RF analogique','hypothesis',[RF],'Existence de varicaps sur revision historique, affectation VHF/UHF sur le PCB etudie non mesuree.')
put_edge(m,'rf','fi_spare','Position FI reservee (historique)','IF/RF','hypothesis',[RF],'Certaines revisions possedent des empreintes non peuplees; non inspectees sur notre carte GD32.')
m['updated']='2026-11-05'
m['diagram_note']='Vue fonctionnelle, pas netlist physique. Sauvegardes RTC/GPS et FI historique distinguent datasheet, photo tierce et continuites manquantes. MCU PRO V1.21.'
p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

p=ROOT/'hardware/models/d578uv-plus-carte-am-observations.json'
m=json.loads(p.read_text(encoding='utf8'))
put_node(m,node('rtc_plus','Sauvegarde RTC PLUS ?', 'logique',345,770,'GD32 VBAT pin 6 - a verifier','Les D578 historiques disposent de sauvegarde RTC. Sur notre PLUS, presence, composant et continuite non mesures par ce dossier.', 'candidate',[BAT,PIN]))
put_node(m,node('gps_plus','GPS ATGM336H PLUS ?', 'peripheriques',665,770,'Reference de la famille, PCB a verifier','GPS familial et la sauvegarde GNSS sont documentes sur D578 anciens ; identification precise du module et du rail sur cette revision PLUS a relever.', 'candidate',[BAT,'docs/peripherals/02_GPS_ATGM336H_UART_NMEA_RAM_PARAMETRES.md']))
put_node(m,node('backup_gps_plus','Sauvegarde hot start PLUS ?', 'peripheriques',665,880,'Composant et montage a verifier','La reference XH414HG est publiee pour des D578 historiques ; le montage de notre PLUS n a pas ete releve dans cette documentation.', 'candidate',[BAT]))
put_node(m,node('protection_plus','Protection alim PLUS ?', 'logique',345,880,'Relais/diode historiques','Relais et diode rapportes par VK7ZJA sur des revisions D578, a verifier sur la carte PLUS.', 'candidate',[RF]))
put_edge(m,'rtc_plus','mcu_plus','RTC backup vers GD32 PLUS ?','Sauvegarde','hypothesis',[BAT],'GD32F303 sur PLUS confirme par utilisateur; reference VBAT pin 6 si meme suffixe de boitier LQFP100, liaison physique non mesuree.')
put_edge(m,'backup_gps_plus','gps_plus','Hot start GNSS PLUS ?','Sauvegarde','hypothesis',[BAT],'Pour D578 historique, deuxieme sauvegarde frontale. Piste GPS de cette carte PLUS non mesuree.')
put_edge(m,'gps_plus','mcu_plus','GNSS -> GD32 PLUS ?','UART candidat','unknown',['docs/peripherals/02_GPS_ATGM336H_UART_NMEA_RAM_PARAMETRES.md'],'Aucun numero de GPIO ni de pin module GPS ne doit etre assigne a ce modele PLUS sans trace.')
put_edge(m,'protection_plus','mcu_plus','Alimentation et protection PLUS','Alimentation','unknown',[RF],'Relais/diode de la famille, schema de la carte PLUS inconnu.')
m['updated']='2026-11-05'
m['diagram_note']='Vue specifiquement PLUS avec GD32F303 confirme utilisateur. Carte RF AM observee. Sauvegardes RTC/GPS issues de comparaison historique, pas de mesure sur cette variante.'
p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Models updated',[(x.name,len(json.loads(x.read_text())['nodes']),len(json.loads(x.read_text())['edges'])) for x in (ROOT/'hardware/models').glob('*.json')])
