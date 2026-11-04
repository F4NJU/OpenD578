"""D578 V9 laboratory controls for external stimuli and observable hardware."""
import argparse,json,time,tkinter as tk
from tkinter import ttk,filedialog,messagebox
from pathlib import Path
from front_window import FrontWindow,VolumeKnob
from lab_inputs import validate_keys,gps_sentences,MIC_CODES
from firmware_input import inspect_image

class LabWindow(FrontWindow):
    def __init__(self,*args,**kwargs):
        self.front_held=set();self.mic_held=set();self.keyboard_down=set()
        super().__init__(*args,**kwargs)
        self.root.title('D578 • Simulateur V10 • GPS et laboratoire')
        self.root.geometry('1140x830');self.root.minsize(1040,760)
        self.root.bind('<KeyPress>',self.keyboard_press)
        self.root.bind('<KeyRelease>',self.keyboard_release)
    def build(self):
        bg='#101820';self.bg=bg
        style=ttk.Style();style.theme_use('clam');style.configure('TButton',padding=(9,5),font=('Segoe UI',10))
        header=tk.Frame(self.root,bg=bg);header.pack(fill='x',padx=20,pady=(10,3))
        tk.Label(header,text='D578',font=('Segoe UI',23,'bold'),fg='#F4F7FB',bg=bg).pack(side='left')
        tk.Label(header,text='  SIMULATEUR V10',font=('Segoe UI',11),fg='#8EA4B7',bg=bg).pack(side='left')
        tk.Label(header,text='Exécution virtuelle • aucun lien avec le poste',fg='#8EA4B7',bg=bg).pack(side='right')
        tk.Label(self.root,textvariable=self.status,fg='#70E0B6',bg=bg,font=('Segoe UI',10)).pack(anchor='w',padx=24)
        self.tabs=ttk.Notebook(self.root);self.tabs.pack(fill='both',expand=True,padx=20,pady=8)
        radio=ttk.Frame(self.tabs);inputs=ttk.Frame(self.tabs);hardware=ttk.Frame(self.tabs);boot=ttk.Frame(self.tabs)
        for frame,title in [(radio,'Radio'),(inputs,'GPS et microphone'),(hardware,'États matériels'),(boot,'Firmware et démarrage')]:self.tabs.add(frame,text=title)
        panel=tk.Frame(radio,bg='#232830',bd=6,relief='ridge');panel.pack(padx=8,pady=12)
        left=tk.Frame(panel,bg='#232830');left.grid(row=0,column=0,padx=10,pady=12)
        self.volume_a=VolumeKnob(left,'Volume A',lambda v:self.send_control('VOLUME_A',value=v));self.volume_a.grid(row=0,column=0)
        self.volume_b=VolumeKnob(left,'Volume B',lambda v:self.send_control('VOLUME_B',value=v));self.volume_b.grid(row=1,column=0)
        power=tk.Frame(left,bg='#232830');power.grid(row=0,column=1,rowspan=2,padx=4,sticky='s')
        self.indicator=tk.Canvas(power,width=26,height=18,bg='#232830',highlightthickness=0);self.indicator.pack(pady=5)
        self.indicator.create_oval(6,3,20,15,fill='#444A48',outline='#7E8C93',tags='led')
        self.power_button=tk.Button(power,text='⏻',font=('Segoe UI',23),fg='#E65A4F',bg='#14191F',width=2,command=self.power)
        self.power_button.pack(pady=5);self.bind_key_button(self.power_button,'POWER',start=True)
        self.face_buttons={}
        for column,names in [(1,['P1','P2','P3','MENU']),(3,['P4','P5','P6','EXIT'])]:
            side=tk.Frame(panel,bg='#232830');side.grid(row=0,column=column,padx=5)
            for name in names:
                b=tk.Button(side,text=name,font=('Segoe UI',11,'bold'),width=6,height=2,bg='#171D25',fg='#BACCF2',command=lambda n=name:self.pulse_front(n))
                b.pack(pady=4);self.face_buttons[name]=b;self.bind_key_button(b,name)
        self.screen_border=tk.Frame(panel,bg='#05090C',padx=8,pady=8);self.screen_border.grid(row=0,column=2,padx=4,pady=8)
        self.screen=tk.Label(self.screen_border,bg='black',borderwidth=0);self.screen.pack()
        dial=tk.Frame(panel,bg='#232830');dial.grid(row=0,column=4,padx=12,pady=30,sticky='n')
        tk.Label(dial,text='Codeur',bg='#232830',fg='#B8C6D2').pack()
        self.dial_push=tk.Button(dial,text='●',font=('Segoe UI',30),bg='#151B22',fg='#94A4B5',width=3,command=lambda:self.pulse_front('DIAL_PUSH'))
        self.dial_push.pack(pady=7);self.bind_key_button(self.dial_push,'DIAL_PUSH')
        for name,label in [('DIAL_DOWN','↶'),('DIAL_UP','↷')]:ttk.Button(dial,text=label,width=5,command=lambda n=name:self.send_control(n)).pack(pady=3)
        self.dial_push.bind('<MouseWheel>',lambda e:self.send_control('DIAL_UP' if e.delta>0 else 'DIAL_DOWN'))
        self.hold_mode=tk.BooleanVar(value=False)
        row=ttk.Frame(radio);row.pack(fill='x',padx=12,pady=3)
        ttk.Checkbutton(row,text='Maintenir les touches après le clic',variable=self.hold_mode).pack(side='left')
        ttk.Button(row,text='Tout relâcher',command=self.release_all).pack(side='left',padx=12)
        self.held_text=tk.StringVar(value='Touches relâchées');ttk.Label(row,textvariable=self.held_text).pack(side='left')
        self.light_text=tk.StringVar(value='Éclairage : en attente du firmware')
        ttk.Label(radio,textvariable=self.light_text).pack(pady=3)
        ttk.Label(radio,text='F1–F6 : P1–P6 · Entrée : MENU · Échap : EXIT · F7 : appui codeur · Espace : PTT micro').pack(pady=3)
        self.build_inputs(inputs);self.build_hardware(hardware);self.build_boot(boot)
        controls=tk.Frame(self.root,bg=bg);controls.pack(pady=(0,5))
        self.start_button=ttk.Button(controls,text='Démarrer',command=self.start);self.start_button.pack(side='left',padx=5)
        self.stop_button=ttk.Button(controls,text='Arrêter la simulation',command=self.stop,state='disabled');self.stop_button.pack(side='left',padx=5)
        self.save_button=ttk.Button(controls,text='Enregistrer l’écran',command=self.save_image);self.save_button.pack(side='left',padx=5)
        self.bt_selector=ttk.Combobox(controls,textvariable=self.bluetooth,values=['Carte absente'],state='readonly',width=16);self.bt_selector.pack(side='left',padx=8)
        tk.Label(self.root,textvariable=self.details,fg='#B8C6D2',bg=bg,font=('Segoe UI',9)).pack(pady=3)
        tk.Label(self.root,textvariable=self.elapsed,fg='#8EA4B7',bg=bg,font=('Segoe UI',9)).pack(pady=(0,8))
    def build_inputs(self,parent):
        gps=ttk.LabelFrame(parent,text='Récepteur GPS simulé • trames NMEA sur USART1');gps.pack(side='left',fill='both',expand=True,padx=12,pady=12)
        self.gps_mode=tk.StringVar(value='Absent');self.latitude=tk.StringVar(value='48.0000');self.longitude=tk.StringVar(value='2.0000');self.gps_utc=tk.StringVar(value='2026-11-04T12:00:00')
        for label,var in [('Latitude de test',self.latitude),('Longitude de test',self.longitude),('UTC initiale',self.gps_utc)]:
            ttk.Label(gps,text=label).pack(anchor='w',padx=12,pady=(10,3));ttk.Entry(gps,textvariable=var,width=28).pack(fill='x',padx=12)
        ttk.Combobox(gps,textvariable=self.gps_mode,values=['Absent','Sans acquisition','Position valide'],state='readonly').pack(fill='x',padx=12,pady=16)
        self.gps_rate=tk.StringVar(value='1')
        cadence=ttk.Frame(gps);cadence.pack(fill='x',padx=12)
        ttk.Label(cadence,text='Trames / seconde simulée').pack(side='left')
        ttk.Combobox(cadence,textvariable=self.gps_rate,values=['1','2','4'],state='readonly',width=5).pack(side='right')
        ttk.Button(gps,text='Appliquer le scénario GPS',command=self.apply_gps).pack(pady=8)
        ttk.Label(gps,text='Le firmware décide de l’acquisition et du déclenchement APRS.\nLe scénario ne modifie aucun indicateur GPS dans sa RAM.',wraplength=390).pack(padx=12,pady=16)
        mic=ttk.LabelFrame(parent,text='Microphone filaire • protocole capturé D578');mic.pack(side='left',fill='both',expand=True,padx=(0,12),pady=12)
        self.microphone=tk.BooleanVar(value=False)
        ttk.Checkbutton(mic,text='Microphone branché',variable=self.microphone,command=lambda:self.send_control('MIC_CONNECT',connected=self.microphone.get())).pack(pady=8)
        self.mic_lock=tk.BooleanVar(value=False)
        ttk.Checkbutton(mic,text='Verrouiller les touches ▲ / ▼',variable=self.mic_lock,
            command=lambda:self.send_control('MIC_LOCK',locked=self.mic_lock.get())).pack(pady=3)
        self.mic_buttons={};keys=ttk.Frame(mic);keys.pack(pady=7)
        layout=[['UP','DOWN','SUB_AB','PTT'],['1','2','3','A'],['4','5','6','B'],['7','8','9','C'],['*','0','#','D']]
        for row,names in enumerate(layout):
            for col,name in enumerate(names):
                b=ttk.Button(keys,text={'UP':'▲','DOWN':'▼','SUB_AB':'A/B'}.get(name,name),width=6,command=lambda n=name:self.pulse_mic(n))
                b.grid(row=row,column=col,padx=3,pady=5);self.mic_buttons[name]=b
                self.bind_key_button(b,name,microphone=True)
        ttk.Checkbutton(mic,text='Maintenir les touches (réglage commun)',variable=self.hold_mode).pack(pady=6)
        ttk.Button(mic,text='Relâcher façade et microphone',command=self.release_all).pack(pady=6)
        ttk.Label(mic,text='PTT + une touche du clavier peuvent être maintenus ensemble.\nLes codes A–D suivent la capture publiée ; leur fonction dépend des réglages OEM.',wraplength=400).pack(padx=12,pady=12)
    def build_hardware(self,parent):
        table=ttk.Frame(parent);table.pack(fill='both',expand=True,padx=12,pady=10)
        self.hw_tree=ttk.Treeview(table,columns=('state','detail'),show='tree headings',height=17)
        self.hw_tree.heading('#0',text='Partie');self.hw_tree.heading('state',text='État observé');self.hw_tree.heading('detail',text='Détail / niveau de preuve')
        self.hw_tree.column('#0',width=145);self.hw_tree.column('state',width=210);self.hw_tree.column('detail',width=610)
        bar=ttk.Scrollbar(table,orient='vertical',command=self.hw_tree.yview);bar.pack(side='right',fill='y')
        self.hw_tree.configure(yscrollcommand=bar.set);self.hw_tree.pack(side='left',fill='both',expand=True)
        for tag,color in [('on','#147D48'),('off','#536271'),('unknown','#946A12'),('tx','#B0202C')]:self.hw_tree.tag_configure(tag,foreground=color)
        for name in ['CPU','GPS','Microphone','PTT','TX','APRS','Ventilateur','Sonde thermique','Alimentation','LCD','NAND','Flash','Modem SCT','RF 0','RF 1','RF 2','RF 3','FM','RTC','Éclairage','USB','Bluetooth','GPIO']:
            self.hw_tree.insert('','end',iid=name,text=name,values=('En attente',''))
        adc=ttk.Frame(parent);adc.pack(fill='x',padx=12,pady=5)
        ttk.Label(adc,text='Sonde thermique ADC6 (valeur brute)').grid(row=0,column=0,sticky='w')
        self.temperature_raw=tk.IntVar(value=262)
        ttk.Scale(adc,from_=0,to=4095,variable=self.temperature_raw,command=lambda v:None).grid(row=0,column=1,sticky='ew',padx=8)
        ttk.Button(adc,text='Appliquer',command=lambda:self.send_control('ADC_RAW',channel=6,value=round(self.temperature_raw.get()))).grid(row=0,column=2)
        ttk.Label(adc,text='Alimentation simulée (V)').grid(row=1,column=0,sticky='w',pady=6)
        self.supply=tk.StringVar(value='13.8');ttk.Entry(adc,textvariable=self.supply,width=10).grid(row=1,column=1,sticky='w',padx=8)
        ttk.Button(adc,text='Appliquer',command=self.apply_voltage).grid(row=1,column=2)
        adc.columnconfigure(1,weight=1)
        ttk.Label(parent,text='Ventilateur : seuils ADC OEM 992 / 868 ; conversion en °C non établie. Les états radio n’impliquent aucune onde RF.').pack(pady=4)
    def build_boot(self,parent):
        self.rtc_mode=tk.StringVar(value='Pile présente');self.boot_mode=tk.StringVar(value='Reprise rapide OEM');self.firmware_path=tk.StringVar()
        for title,var,values in [('Démarrage',self.boot_mode,['Reprise rapide OEM','Reset application','Reset bootloader (diagnostic)']),('Pile RTC',self.rtc_mode,['Pile présente','Pile vide'])]:
            row=ttk.Frame(parent);row.pack(fill='x',padx=24,pady=12);ttk.Label(row,text=title,width=22).pack(side='left')
            ttk.Combobox(row,textvariable=var,values=values,state='readonly',width=35).pack(side='left')
        row=ttk.Frame(parent);row.pack(fill='x',padx=24,pady=12)
        ttk.Label(row,text='Firmware à essayer',width=22).pack(side='left');ttk.Entry(row,textvariable=self.firmware_path).pack(side='left',fill='x',expand=True)
        ttk.Button(row,text='Choisir…',command=self.browse_firmware).pack(side='left',padx=6)
        ttk.Button(row,text='OEM fourni',command=lambda:self.firmware_path.set('')).pack(side='left')
        ttk.Label(parent,text='Application brute .CDD/.bin à 0x08006000 ou Flash complète de 3 Mio.\nUn fichier sélectionné impose un reset ; la reprise OEM ne valide pas ce firmware.\nLe modèle matériel reste fondé sur le D578 GD32 V1.21.',wraplength=970).pack(anchor='w',padx=24,pady=8)
        row=ttk.Frame(parent);row.pack(fill='x',padx=24,pady=12)
        ttk.Label(row,text='Archives du projet',width=22).pack(side='left');ttk.Entry(row,textvariable=self.source).pack(side='left',fill='x',expand=True)
        ttk.Button(row,text='Choisir…',command=self.browse_source).pack(side='left',padx=6)
        ttk.Button(parent,text='Maintenir P2 + appui codeur au lancement',command=lambda:self.set_preset(['P2','DIAL_PUSH'])).pack(anchor='w',padx=24,pady=12)
        ttk.Button(parent,text='Test GPS : P3 + appui codeur au lancement',command=lambda:self.set_preset(['P3','DIAL_PUSH'])).pack(anchor='w',padx=24,pady=4)
        ttk.Button(parent,text='GPS RSSI : EXIT + appui codeur au lancement',command=lambda:self.set_preset(['EXIT','DIAL_PUSH'])).pack(anchor='w',padx=24,pady=4)
        ttk.Button(parent,text='Tout relâcher',command=self.release_all).pack(anchor='w',padx=24)
        ttk.Label(parent,text='Les préréglages sélectionnent un reset application avec les touches maintenues.\nLes trois écrans ont été obtenus en exécutant le firmware OEM.\nDeux touches d’un même groupe ADC restent non qualifiées électriquement.',wraplength=960).pack(anchor='w',padx=24,pady=15)
    def bind_key_button(self,button,name,microphone=False,start=False):
        def press(event):
            self.key_change(name,True,microphone)
            if start and (self.process is None or self.process.poll() is not None):self.start()
            return 'break'
        def release(event):self.key_change(name,False,microphone);return 'break'
        button.bind('<ButtonPress-1>',press);button.bind('<ButtonRelease-1>',release)
    def key_change(self,name,down,microphone=False):
        current=self.mic_held if microphone else self.front_held
        if self.hold_mode.get() and not down:return
        updated=set(current)
        if down:
            if self.hold_mode.get() and name in updated:updated.remove(name)
            else:updated.add(name)
        else:updated.discard(name)
        try:
            if microphone:
                from lab_inputs import microphone_frame
                microphone_frame(updated)
                if not self.microphone.get():self.microphone.set(True);self.send_control('MIC_CONNECT',connected=True)
                self.mic_held=updated;self.send_control('MIC_KEYS',keys=sorted(updated))
            else:self.front_held=validate_keys(updated);self.send_control('KEY_SET',keys=sorted(updated))
            self.update_held()
        except ValueError as error:self.status.set(str(error))
    def update_held(self):
        self.held_text.set('Maintenues : '+', '.join([*sorted(self.front_held),*['micro '+k for k in sorted(self.mic_held)]]) if self.front_held or self.mic_held else 'Touches relâchées')
        for name,b in self.face_buttons.items():b.configure(relief='sunken' if name in self.front_held else 'raised')
    def pulse_front(self,name):
        self.key_change(name,True)
        if not self.hold_mode.get():self.root.after(250,lambda:self.key_change(name,False))
    def pulse_mic(self,name):
        self.key_change(name,True,True)
        if not self.hold_mode.get():self.root.after(250,lambda:self.key_change(name,False,True))
    def release_all(self):
        self.front_held=set();self.mic_held=set();self.keyboard_down=set();self.update_held();self.send_control('RELEASE_ALL')
    def set_preset(self,keys):
        self.front_held=validate_keys(keys);self.hold_mode.set(True);self.update_held()
        self.boot_mode.set('Reset application')
        self.send_control('KEY_SET',keys=sorted(keys))
    def keyboard_press(self,event):
        if isinstance(self.root.focus_get(),(tk.Entry,ttk.Entry,ttk.Combobox,tk.Text)):return
        mapping={**{f'F{i}':f'P{i}' for i in range(1,7)},'Return':'MENU','Escape':'EXIT','F7':'DIAL_PUSH','space':'PTT'}
        if event.keysym in mapping and event.keysym not in self.keyboard_down:
            self.keyboard_down.add(event.keysym);self.key_change(mapping[event.keysym],True,event.keysym=='space')
    def keyboard_release(self,event):
        mapping={**{f'F{i}':f'P{i}' for i in range(1,7)},'Return':'MENU','Escape':'EXIT','F7':'DIAL_PUSH','space':'PTT'}
        if event.keysym in self.keyboard_down:
            self.keyboard_down.discard(event.keysym);self.key_change(mapping[event.keysym],False,event.keysym=='space')
    def apply_gps(self):
        try:
            mode={'Absent':'absent','Sans acquisition':'no_fix','Position valide':'fix'}[self.gps_mode.get()]
            latitude=float(self.latitude.get());longitude=float(self.longitude.get());gps_sentences(latitude,longitude,self.gps_utc.get(),mode=='fix')
            self.send_control('GPS',mode=mode,latitude=latitude,longitude=longitude,utc=self.gps_utc.get(),hertz=int(self.gps_rate.get()))
        except ValueError as error:self.status.set(str(error))
    def apply_voltage(self):
        try:self.send_control('VOLTAGE',volts=float(self.supply.get()))
        except ValueError:self.status.set('Entrer une tension numérique')
    def browse_firmware(self):
        result=filedialog.askopenfilename(title='Firmware pour la mémoire virtuelle',filetypes=[('Application ou Flash','*.CDD *.cdd *.bin'),('Tous les fichiers','*.*')])
        if result:self.firmware_path.set(result);self.boot_mode.set('Reset application')
    def extra_launch_arguments(self):
        firmware=self.firmware_path.get().strip();entry='bootloader' if self.boot_mode.get().startswith('Reset bootloader') else 'application'
        args=['--rtc-mode','empty' if self.rtc_mode.get()=='Pile vide' else 'retained','--entry',entry]
        if firmware:inspect_image(firmware);args.extend(['--firmware',firmware])
        elif self.boot_mode.get()=='Reprise rapide OEM' and self.rtc_mode.get()!='Pile vide':args.append('--resume-ready')
        if self.microphone.get():args.append('--microphone')
        if self.mic_lock.get():args.append('--mic-lock')
        if self.front_held:args.extend(['--initial-keys',','.join(sorted(self.front_held))])
        mode={'Absent':'absent','Sans acquisition':'no_fix','Position valide':'fix'}[self.gps_mode.get()]
        gps_sentences(float(self.latitude.get()),float(self.longitude.get()),self.gps_utc.get(),mode=='fix')
        args.extend(['--gps',mode,'--latitude',self.latitude.get(),'--longitude',self.longitude.get(),'--gps-utc',self.gps_utc.get()])
        args.extend(['--gps-rate',self.gps_rate.get()])
        volts=float(self.supply.get())
        if not 5<=volts<=30:raise ValueError('Tension de test : choisir 5 à 30 V')
        args.extend(['--voltage',str(volts)])
        return args
    def start(self):
        try:self.extra_launch_arguments()
        except (ValueError,OSError) as error:messagebox.showerror('Paramètres de simulation',str(error));return
        super().start()
        if self.mic_held:self.send_control('MIC_KEYS',keys=sorted(self.mic_held))
    def poll(self):
        super().poll()
        try:
            state=json.loads((self.run_directory/'status.json').read_text(encoding='utf-8'));h=state.get('hardware',{})
            if not h:return
            def row(name,value,detail='',tag='off'):self.hw_tree.item(name,values=(value,detail),tags=(tag,))
            row('CPU',f"{state.get('steps',0):,} instructions",'Cadence logique, modèle non précis au cycle')
            gps=h['gps_OEM'];locked=gps.get('module_detected') and gps.get('position_fix')
            row('GPS','Acquis OEM' if locked else 'Présent, non acquis' if gps['module_detected'] else 'Absent OEM',f"Entrée : {h['gps_input']['mode']} · {gps['parser_bytes']} octets traités",'on' if locked else 'unknown')
            mic=h['microphone'];row('Microphone','Branché' if mic['connected'] else 'Absent',f"{mic['received_bytes']} octets RX · pertes : {mic['overruns']}")
            row('PTT','Appuyé' if 'PTT' in mic['held_keys'] else 'Relâché','État du bouton simulé ; distinct de l’émission OEM')
            tx=h['TX'];row('TX','Demandé par OEM' if tx['native_request'] else 'Non demandé OEM','État natif utilisé par la logique du ventilateur ; aucune onde RF','tx' if tx['native_request'] else 'off')
            aprs=h['APRS'];row('APRS',f"Minuterie OEM : {aprs['native_countdown']}",f"Canal : {aprs['channel_mode_raw']} · entrées modulateur : {aprs['modulator_entries']} · DMA6 : {aprs['DMA6_enabled']}")
            fan=h['FAN'];row('Ventilateur','Commande ON' if fan['command_on'] else 'Commande OFF' if fan['command_on'] is not None else 'Inconnu',fan['mode']+' · registre radio 25h bit 1','on' if fan['command_on'] else 'off')
            row('Sonde thermique',str(fan['ADC6_raw'])+' brut','Hystérésis OEM : ON ≥ 992 / OFF ≤ 868 ; °C non étalonnés')
            row('Alimentation',f"{h['ADC']['supply_volts_OEM']:.1f} V",'Valeur convertie par le firmware OEM')
            row('LCD','Allumé' if h['LCD']['display_on'] else 'Éteint',f"Rétroéclairage : {h['LCD']['brightness']}")
            for name in ['NAND','Flash']:row(name,f"{h[name]['erases']} eff. / {h[name]['programs']} prog.",'Depuis le début de cette exécution')
            row('Modem SCT','Chargeur reçu' if h['SCT']['boot_complete'] else 'En attente',f"{h['SCT']['packets']} paquets observés ; DSP/audio non exécutés")
            for bank in range(4):
                value=h['RF_banks'][str(bank)];row('RF '+str(bank),f"{value['transactions']} transactions",'Sélection '+value['selector']+' ; état des ondes non simulé')
            row('FM',f"{h['FM']['transactions']} échanges",'Bus du récepteur FM ; aucune station simulée')
            row('RTC',h['RTC']['battery_mode'],'Domaine de sauvegarde synthétique')
            row('Éclairage','Registres observés',str(h['lighting_registers']))
            row('USB','Sans hôte');row('Bluetooth',h['Bluetooth']['peer'])
            row('GPIO','Sorties observées',' · '.join(f'{k}: {v}' for k,v in h['GPIO_outputs'].items()))
            if not h.get('OEM_state_interpretation_qualified',True):
                for name in ['GPS','TX','APRS','Ventilateur','Sonde thermique','Alimentation']:
                    self.hw_tree.item(name,values=('Interprétation à valider','Firmware sélectionné : les adresses et conventions OEM peuvent avoir changé'),tags=('unknown',))
        except (OSError,ValueError,KeyError):pass

def main():
    p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true');p.add_argument('--screenshot',type=Path);p.add_argument('--show-tab',type=int,choices=range(4),default=0);a=p.parse_args()
    root=tk.Tk()
    if a.self_test:root.geometry('+10000+10000')
    app=LabWindow(root)
    if a.self_test:root.geometry('+10000+10000')
    if not a.self_test:root.mainloop();return
    root.update();assert all(b.winfo_ismapped() for b in app.face_buttons.values())
    assert app.tabs.index('end')==4
    # Check each page fits its notebook, including at the minimum supported size.
    for width,height in [(1140,830),(1040,760)]:
        root.geometry(f'{width}x{height}+10000+10000');root.update()
        for index in range(4):
            app.tabs.select(index);root.update()
            page=root.nametowidget(app.tabs.select())
            def check(widget):
                for child in widget.winfo_children():
                    if not child.winfo_ismapped():continue
                    assert child.winfo_x()>=-1 and child.winfo_y()>=-1,str(child)
                    assert child.winfo_x()+child.winfo_width()<=widget.winfo_width()+2,(str(child),'width')
                    assert child.winfo_y()+child.winfo_height()<=widget.winfo_height()+2,(str(child),'height')
                    check(child)
            check(page)
    app.tabs.select(0);root.update()
    class Fake:
        def poll(self):return None
    from simulator_window import ROOT
    app.process=Fake();app.run_directory=ROOT/'work/window_v9_test';app.run_directory.mkdir(parents=True,exist_ok=True)
    for path in app.run_directory.glob('input_*.json'):path.unlink()
    app.hold_mode.set(True);app.key_change('P2',True);app.key_change('DIAL_PUSH',True)
    assert app.front_held=={'P2','DIAL_PUSH'}
    app.key_change('P1',True);assert app.front_held=={'P2','DIAL_PUSH'}
    app.release_all();app.key_change('PTT',True,True);app.key_change('UP',True,True)
    assert app.mic_held=={'PTT','UP'}
    app.release_all();app.gps_mode.set('Position valide');app.apply_gps()
    values=[json.loads(path.read_text()) for path in sorted(app.run_directory.glob('input_*.json'))]
    assert any(v.get('keys')==['DIAL_PUSH','P2'] for v in values)
    assert any(v['control']=='GPS' for v in values)
    app.firmware_path.set('selected-test.bin');app.boot_mode.set('Reprise rapide OEM')
    assert 'Reprise rapide OEM' in app.boot_mode.get()
    app.firmware_path.set('');app.process=None
    app.set_preset(['P3','DIAL_PUSH'])
    assert app.boot_mode.get()=='Reset application' and '--resume-ready' not in app.extra_launch_arguments()
    app.microphone.set(True);app.mic_lock.set(True)
    assert '--mic-lock' in app.extra_launch_arguments()
    app.release_all()
    app.status.set('Capture OEM enregistrée • cliquer Démarrer pour exécuter le firmware')
    app.tabs.select(a.show_tab)
    if a.screenshot:
        from window_capture import capture_window
        root.update();a.screenshot.parent.mkdir(parents=True,exist_ok=True)
        def capture():
            capture_window(root,a.screenshot)
            root.quit()
        root.after(600,capture);root.mainloop()
    print(json.dumps(dict(window=[root.winfo_width(),root.winfo_height()],tabs=4,atomic_front_chord=True,
        same_ADC_group_rejected=True,PTT_plus_key=True,GPS_command=True,firmware_selector=True,startup_presets_force_reset=True,microphone_lock_at_launch=True,tab_bounds_checked_at_two_sizes=True)))
    root.destroy()
if __name__=='__main__':main()
