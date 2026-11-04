"""D578 faceplate: authentic firmware LCD and external input controls."""
import argparse,json,time,math,tkinter as tk
from tkinter import ttk
from pathlib import Path
from PIL import Image,ImageTk,ImageEnhance
from simulator_window import SimulatorWindow,ROOT


class VolumeKnob(tk.Canvas):
    def __init__(self,parent,title,command):
        super().__init__(parent,width=80,height=86,bg='#232830',highlightthickness=0)
        self.value=1800
        self.command=command
        self.create_text(40,8,text=title,fill='#D6DFEA',font=('Segoe UI',9))
        self.create_oval(13,23,67,77,fill='#111820',outline='#667787',width=3)
        self.needle=self.create_line(40,50,40,28,fill='#C6D9F7',width=3)
        self.set(self.value)
        self.bind('<MouseWheel>',lambda event:self.adjust(120 if event.delta>0 else -120))
        self.bind('<Button-1>',self.grab)
        self.bind('<B1-Motion>',self.drag)

    def set(self,value):
        self.value=max(0,min(4095,int(value)))
        angle=math.radians(225-270*self.value/4095)
        self.coords(self.needle,40,50,40+21*math.cos(angle),50-21*math.sin(angle))

    def adjust(self,delta):
        self.set(self.value+delta)
        self.command(self.value)

    def grab(self,event):self.drag_y=event.y

    def drag(self,event):
        self.adjust((self.drag_y-event.y)*35)
        self.drag_y=event.y


class FrontWindow(SimulatorWindow):
    def __init__(self,*args,**kwargs):
        self.input_serial=0
        self.brightness=255
        super().__init__(*args,**kwargs)
        self.root.title('D578 • Simulateur V8')
        self.root.geometry('1100x665')
        self.root.minsize(1020,620)

    def build(self):
        bg='#101820'
        style=ttk.Style()
        style.theme_use('clam')
        style.configure('TButton',padding=(10,7),font=('Segoe UI',10))
        heading=tk.Frame(self.root,bg=bg)
        heading.pack(fill='x',padx=24,pady=(18,6))
        tk.Label(heading,text='D578',font=('Segoe UI',25,'bold'),fg='#F4F7FB',bg=bg).pack(side='left')
        tk.Label(heading,text=' SIMULATEUR V8',font=('Segoe UI',11),fg='#8EA4B7',bg=bg).pack(side='left',padx=10)
        tk.Label(self.root,textvariable=self.status,font=('Segoe UI',11),fg='#70E0B6',bg=bg).pack(anchor='w',padx=26,pady=(0,8))
        panel=tk.Frame(self.root,bg='#232830',bd=6,relief='ridge')
        panel.pack(padx=20,pady=6)
        left=tk.Frame(panel,bg='#232830')
        left.grid(row=0,column=0,padx=12,pady=12)
        self.volume_a=VolumeKnob(left,'Volume A',lambda value:self.send_control('VOLUME_A',value=value))
        self.volume_a.grid(row=0,column=0)
        self.volume_b=VolumeKnob(left,'Volume B',lambda value:self.send_control('VOLUME_B',value=value))
        self.volume_b.grid(row=1,column=0)
        power=tk.Frame(left,bg='#232830')
        power.grid(row=0,column=1,rowspan=2,padx=(4,0),sticky='s')
        self.indicator=tk.Canvas(power,width=26,height=18,bg='#232830',highlightthickness=0)
        self.indicator.pack(pady=(0,5))
        self.indicator.create_oval(6,3,20,15,fill='#444A48',outline='#7E8C93',tags='led')
        self.power_button=tk.Button(power,text='⏻',font=('Segoe UI',23),fg='#E65A4F',bg='#14191F',
            width=2,command=self.power)
        self.power_button.pack(pady=(0,5))
        self.face_buttons={}
        for column,names in ((1,['P1','P2','P3','MENU']),(3,['P4','P5','P6','EXIT'])):
            side=tk.Frame(panel,bg='#232830')
            side.grid(row=0,column=column,padx=6)
            for name in names:
                button=tk.Button(side,text=name,font=('Segoe UI',11,'bold'),width=6,height=2,
                    bg='#171D25',fg='#BACCF2',activebackground='#37465C',activeforeground='white',
                    command=lambda name=name:self.send_control(name))
                button.pack(pady=4)
                self.face_buttons[name]=button
        self.screen_border=tk.Frame(panel,bg='#05090C',padx=8,pady=8)
        self.screen_border.grid(row=0,column=2,padx=5,pady=8)
        self.screen=tk.Label(self.screen_border,bg='black',borderwidth=0)
        self.screen.pack()
        dial=tk.Frame(panel,bg='#232830')
        dial.grid(row=0,column=4,padx=12,sticky='n',pady=30)
        tk.Label(dial,text='Canal / sélection',bg='#232830',fg='#B8C6D2',font=('Segoe UI',9)).pack()
        self.dial_push=tk.Button(dial,text='●',font=('Segoe UI',30),bg='#151B22',fg='#94A4B5',width=3,
            command=lambda:self.send_control('DIAL_PUSH'))
        self.dial_push.pack(pady=7)
        row=tk.Frame(dial,bg='#232830')
        row.pack()
        ttk.Button(row,text='↶',width=3,command=lambda:self.send_control('DIAL_DOWN')).pack(side='left')
        ttk.Button(row,text='↷',width=3,command=lambda:self.send_control('DIAL_UP')).pack(side='left',padx=3)
        self.dial_push.bind('<MouseWheel>',lambda event:self.send_control('DIAL_UP' if event.delta>0 else 'DIAL_DOWN'))
        tk.Label(dial,text='Appuyer : valider\nou champ suivant',bg='#232830',fg='#8EA4B7',font=('Segoe UI',9)).pack(pady=10)
        self.light_text=tk.StringVar(value='Éclairage : commande du firmware non encore relevée')
        tk.Label(self.root,textvariable=self.light_text,bg=bg,fg='#A6B5C3',font=('Segoe UI',9)).pack(pady=4)
        tk.Label(self.root,textvariable=self.details,font=('Segoe UI',10),fg='#B8C6D2',bg=bg).pack(pady=4)
        controls=tk.Frame(self.root,bg=bg)
        controls.pack(pady=6)
        self.start_button=ttk.Button(controls,text='Démarrer',command=self.start)
        self.start_button.pack(side='left',padx=4)
        self.stop_button=ttk.Button(controls,text='Arrêter la simulation',command=self.stop,state='disabled')
        self.stop_button.pack(side='left',padx=4)
        self.save_button=ttk.Button(controls,text='Enregistrer l’écran',command=self.save_image)
        self.save_button.pack(side='left',padx=4)
        self.bt_selector=ttk.Combobox(controls,textvariable=self.bluetooth,values=['Carte absente'],state='readonly',width=15)
        self.bt_selector.pack(side='left',padx=10)
        pathrow=tk.Frame(self.root,bg=bg)
        pathrow.pack(fill='x',padx=28,pady=8)
        tk.Label(pathrow,text='Archives du projet',fg='#B8C6D2',bg=bg,font=('Segoe UI',10)).pack(side='left',padx=(0,10))
        ttk.Entry(pathrow,textvariable=self.source).pack(side='left',fill='x',expand=True)
        ttk.Button(pathrow,text='Choisir…',command=self.browse_source).pack(side='left',padx=(8,0))
        clockrow=tk.Frame(self.root,bg=bg)
        clockrow.pack(pady=3)
        self.rtc_mode=tk.StringVar(value='Pile présente')
        self.rtc_selector=ttk.Combobox(clockrow,textvariable=self.rtc_mode,values=['Pile présente','Pile vide'],state='readonly',width=17)
        self.rtc_selector.pack(side='left',padx=7)
        self.boot_mode=tk.StringVar(value='Reprise rapide')
        ttk.Combobox(clockrow,textvariable=self.boot_mode,values=['Reprise rapide','Démarrage complet'],state='readonly',width=19).pack(side='left',padx=5)
        tk.Label(clockrow,text='Date initiale simulée : 04/11/2026 12:00 • micro débranché',fg='#8EA4B7',bg=bg,font=('Segoe UI',9)).pack(side='left')
        tk.Label(self.root,textvariable=self.elapsed,font=('Segoe UI',9),fg='#8EA4B7',bg=bg).pack(pady=6)

    def render(self):
        if self.raw_image is None:return
        source=self.view_image()
        shown=ImageEnhance.Brightness(source).enhance(self.brightness/255)
        zoom=3
        scaled=shown.resize((source.width*zoom,source.height*zoom),Image.Resampling.NEAREST)
        self.frame_image=ImageTk.PhotoImage(scaled)
        self.screen.configure(image=self.frame_image)

    def send_control(self,control,**extra):
        if self.process is None or self.process.poll() is not None:return
        self.input_serial+=1
        path=self.run_directory/f'input_{time.time_ns()}_{self.input_serial:05}.json'
        temporary=path.with_suffix('.tmp')
        temporary.write_text(json.dumps(dict(control=control,**extra)),encoding='utf-8')
        temporary.replace(path)

    def power(self):
        if self.process is None or self.process.poll() is not None:self.start()
        else:self.send_control('POWER')

    def extra_launch_arguments(self):
        args=['--rtc-mode','empty' if self.rtc_mode.get()=='Pile vide' else 'retained']
        if self.boot_mode.get()=='Reprise rapide' and self.rtc_mode.get()!='Pile vide':args.append('--resume-ready')
        return args

    def start(self):
        self.brightness=255
        super().start()

    def poll(self):
        super().poll()
        try:
            state=json.loads((self.run_directory/'status.json').read_text(encoding='utf-8'))
            if state.get('running') and state.get('application_running'):
                self.status.set('Simulation en cours • reprise rapide' if state.get('quick_resume') else 'Simulation en cours')
            lights=state.get('lighting',{})
            brightness=lights.get('lcd_brightness')
            if brightness is not None:
                self.light_text.set(f'Rétroéclairage LCD : {round(brightness*100/255)} % • Couleurs des LED de touches à confirmer')
                if self.brightness!=brightness:
                    self.brightness=brightness
                    self.render()
        except (OSError,ValueError):pass

    @staticmethod
    def friendly_stop(stop):
        if stop.get('kind')=='instruction_budget':return 'limite de calcul atteinte'
        if stop.get('kind','').startswith('SCT3258 packet outside'):
            return 'échange du processeur DMR à compléter'
        return SimulatorWindow.friendly_stop(stop)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--reference-dir',type=Path)
    parser.add_argument('--source-dir',type=Path)
    parser.add_argument('--cache-dir',type=Path)
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    root=tk.Tk()
    app=FrontWindow(root,args.reference_dir,args.source_dir,args.cache_dir)
    if args.self_test:
        root.update()
        assert list(app.face_buttons)==['P1','P2','P3','MENU','P4','P5','P6','EXIT']
        assert all(x.winfo_ismapped() for x in app.face_buttons.values())
        assert app.volume_a.winfo_ismapped() and app.dial_push.winfo_ismapped()
        assert app.face_buttons['P1'].winfo_rootx()<app.screen.winfo_rootx()<app.face_buttons['P4'].winfo_rootx()
        assert app.indicator.winfo_rooty()<app.power_button.winfo_rooty()
        class FakeProcess:
            def poll(self):return None
        app.process=FakeProcess()
        app.run_directory=ROOT/'work'/'window_self_test'
        app.run_directory.mkdir(parents=True,exist_ok=True)
        app.face_buttons['MENU'].invoke()
        app.power()
        app.volume_a.adjust(120)
        paths=sorted(app.run_directory.glob('input_*.json'))
        observed=[json.loads(p.read_text()) for p in paths]
        assert [x['control'] for x in observed]==['MENU','POWER','VOLUME_A']
        for path in paths:path.unlink()
        app.process=None
        print(json.dumps(dict(window=[root.winfo_width(),root.winfo_height()],lcd=[app.frame_image.width(),app.frame_image.height()],
                              faceplate_controls_visible=True,buttons_generate_external_input_commands=True,
                              power_distinct_from_simulator_stop=True)))
        root.destroy()
    else:root.mainloop()


if __name__=='__main__':main()
