#!/usr/bin/env python3
"""A responsive Windows/Tk window displaying captured OEM LCD pixels."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

ROOT = Path(__file__).resolve().parent


class SimulatorWindow:
    def __init__(self, root, reference_directory=None, source_directory=None, cache_directory=None):
        self.root = root
        self.root.title('D578 • Simulateur LCD')
        self.root.configure(bg='#101820')
        self.root.geometry('910x790')
        self.root.minsize(760, 760)
        self.process = None
        self.process_log = None
        self.run_directory = ROOT/'results'/'local'
        self.cache_directory = Path(cache_directory) if cache_directory else ROOT/'work'/'inputs'
        self.image_path = None
        self.image_mtime = None
        self.frame_image = None
        self.raw_image = None
        self.orientation = tk.StringVar(value='Paysage D578')
        self.scale = tk.IntVar(value=4)
        self.status = tk.StringVar(value='Capture enregistrée du démarrage OEM')
        self.details = tk.StringVar(value='Pixels reconstruits depuis les écritures GPIO du firmware.')
        self.source = tk.StringVar(value=str(source_directory or Path.home()/'Downloads'/'D578'))
        self.bluetooth = tk.StringVar(value='Carte absente')
        self.elapsed = tk.StringVar(value='Simulation sur PC • cadence logique • aucun accès au poste')
        self.build()
        reference = Path(reference_directory) if reference_directory else ROOT/'results'/'reference'
        if (reference/'lcd.png').exists():
            self.load_frame(reference/'lcd.png')
        else:
            self.raw_image = Image.new('RGB',(129,161))
            self.render()
            self.status.set('Prêt à démarrer')
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.root.after(300, self.poll)

    def build(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', padding=(13,9), font=('Segoe UI',10))
        style.configure('TCombobox', padding=5)
        header = tk.Frame(self.root,bg='#101820')
        header.pack(fill='x',padx=26,pady=(20,12))
        tk.Label(header,text='D578',font=('Segoe UI',25,'bold'),fg='#F4F7FB',bg='#101820').pack(side='left')
        tk.Label(header,text=' SIMULATEUR LCD',font=('Segoe UI',11),fg='#8EA4B7',bg='#101820').pack(side='left',padx=(10,0),pady=(10,0))
        tk.Label(self.root,textvariable=self.status,font=('Segoe UI',12),fg='#70E0B6',bg='#101820').pack(anchor='w',padx=28,pady=(0,10))
        self.screen_border = tk.Frame(self.root,bg='#2A3540',padx=12,pady=12)
        self.screen_border.pack(padx=24,pady=4)
        self.screen = tk.Label(self.screen_border,bg='black',borderwidth=0)
        self.screen.pack()
        tk.Label(self.root,textvariable=self.details,font=('Segoe UI',10),fg='#B8C6D2',bg='#101820',wraplength=820).pack(padx=24,pady=(12,8))
        controls=tk.Frame(self.root,bg='#101820')
        controls.pack(pady=7)
        self.start_button=ttk.Button(controls,text='Démarrer avec Power',command=self.start)
        self.start_button.pack(side='left',padx=4)
        self.stop_button=ttk.Button(controls,text='Arrêter',command=self.stop,state='disabled')
        self.stop_button.pack(side='left',padx=4)
        self.save_button=ttk.Button(controls,text='Enregistrer l’écran',command=self.save_image)
        self.save_button.pack(side='left',padx=4)
        selector=tk.Frame(self.root,bg='#101820')
        selector.pack(pady=8)
        tk.Label(selector,text='Vue',font=('Segoe UI',10),fg='#B8C6D2',bg='#101820').pack(side='left',padx=7)
        orientation=ttk.Combobox(selector,textvariable=self.orientation,values=['Paysage D578','Trame brute'],state='readonly',width=18)
        orientation.pack(side='left',padx=4)
        orientation.bind('<<ComboboxSelected>>',lambda event:self.render())
        tk.Label(selector,text='Bluetooth',font=('Segoe UI',10),fg='#B8C6D2',bg='#101820').pack(side='left',padx=(20,7))
        self.bt_selector=ttk.Combobox(selector,textvariable=self.bluetooth,values=['Carte absente'],state='readonly',width=20)
        self.bt_selector.pack(side='left')
        pathrow=tk.Frame(self.root,bg='#101820')
        pathrow.pack(fill='x',padx=28,pady=(8,5))
        tk.Label(pathrow,text='Archives du projet',font=('Segoe UI',10),fg='#B8C6D2',bg='#101820').pack(anchor='w',pady=(0,5))
        ttk.Entry(pathrow,textvariable=self.source).pack(side='left',fill='x',expand=True)
        ttk.Button(pathrow,text='Choisir…',command=self.browse_source).pack(side='left',padx=(8,0))
        tk.Label(self.root,textvariable=self.elapsed,font=('Segoe UI',9),fg='#8EA4B7',bg='#101820').pack(pady=(12,6))

    def browse_source(self):
        result=filedialog.askdirectory(title='Dossier contenant les archives originales D578')
        if result:
            self.source.set(result)

    def load_frame(self,path):
        with Image.open(path) as image:
            self.raw_image=image.convert('RGB').copy()
        self.image_path=path
        self.render()

    def view_image(self):
        if self.orientation.get()=='Paysage D578':
            return self.raw_image.transpose(Image.Transpose.TRANSPOSE)
        return self.raw_image

    def render(self):
        if self.raw_image is None:
            return
        source=self.view_image()
        # Preserve every captured address pixel, including the border. The
        # landscape transform is a display interpretation; raw data is saved.
        zoom=min(4, max(1, 650//source.width), max(1, 450//source.height))
        scaled=source.resize((source.width*zoom,source.height*zoom),Image.Resampling.NEAREST)
        self.frame_image=ImageTk.PhotoImage(scaled)
        self.screen.configure(image=self.frame_image)

    def start(self):
        if self.process is not None and self.process.poll() is None:
            return
        source=Path(self.source.get())
        required=['AT-D578 PRO PC SOFTWARE.zip','D578_PASSATION_PHASE47_NAND_COMPLETE_2026-11-03.zip']
        if not all((source/name).is_file() for name in required):
            messagebox.showerror('Archives manquantes','Choisissez le dossier contenant les deux archives sources du projet.')
            return
        self.run_directory.mkdir(parents=True,exist_ok=True)
        marker=self.run_directory/'stop.request'
        if marker.exists():
            marker.unlink()
        for pending_input in self.run_directory.glob('input_*.json'):
            pending_input.unlink()
        old_frame=self.run_directory/'lcd.png'
        self.image_mtime=old_frame.stat().st_mtime_ns if old_frame.exists() else None
        self.raw_image=Image.new('RGB',(129,161))
        self.render()
        self.status.set('Préparation du démarrage…')
        self.details.set('Vérification du firmware et de la NAND ; Power sera simulé après la veille initiale.')
        command=[sys.executable,str(ROOT/'run_lcd.py'),'--source-dir',str(source),
                 '--out-dir',str(self.run_directory),'--cache-dir',str(self.cache_directory),
                 '--bluetooth','absent' if self.bluetooth.get()=='Carte absente' else 'et12']
        command.extend(self.extra_launch_arguments())
        self.process_log=(self.run_directory/'lancement.log').open('w',encoding='utf-8')
        flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
        self.process=subprocess.Popen(command,stdout=self.process_log,stderr=subprocess.STDOUT,creationflags=flags)
        self.start_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        self.bt_selector.configure(state='disabled')

    def extra_launch_arguments(self):
        return []

    def stop(self):
        if self.process is not None and self.process.poll() is None:
            (self.run_directory/'stop.request').write_text('stop',encoding='ascii')
            self.status.set('Arrêt demandé…')

    def poll(self):
        if self.process is not None:
            state=self.run_directory/'status.json'
            try:
                data=json.loads(state.read_text(encoding='utf-8'))
                if data.get('phase'):
                    self.status.set(data['phase'])
                elif data.get('running'):
                    self.status.set('Démarrage du firmware en cours…')
                else:
                    stop=data.get('stop') or {}
                    self.status.set('Exécution arrêtée • '+self.friendly_stop(stop))
                self.details.set(f"{data.get('steps',0):,} instructions  ·  {data.get('pixels',0):,} pixels LCD écrits  ·  {data.get('NAND_buffers',0)} lectures NAND vérifiées".replace(',',' '))
            except (OSError,ValueError):
                pass
            frame=self.run_directory/'lcd.png'
            try:
                mtime=frame.stat().st_mtime_ns
                if mtime != self.image_mtime:
                    self.load_frame(frame)
                    self.image_mtime=mtime
            except OSError:
                pass
            code=self.process.poll()
            if code is not None:
                if self.process_log:
                    self.process_log.close()
                    self.process_log=None
                self.process=None
                self.start_button.configure(state='normal')
                self.stop_button.configure(state='disabled')
                self.bt_selector.configure(state='readonly')
                if code:
                    self.status.set('La simulation a rencontré une erreur ; voir le journal dans results/local.')
        self.root.after(300,self.poll)

    @staticmethod
    def friendly_stop(stop):
        if stop.get('address')=='0x40013810':
            return 'USART0 reste à modéliser'
        if stop.get('kind')=='stopped by simulator user':
            return 'arrêt demandé'
        return stop.get('kind','simulation terminée')

    def save_image(self):
        path=filedialog.asksaveasfilename(title='Enregistrer la capture LCD',defaultextension='.png',filetypes=[('Image PNG','*.png')])
        if path:
            self.view_image().save(path)

    def close(self):
        self.stop()
        self.root.destroy()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--reference-dir',type=Path)
    parser.add_argument('--source-dir',type=Path)
    parser.add_argument('--cache-dir',type=Path)
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    root=tk.Tk()
    app=SimulatorWindow(root,args.reference_dir,args.source_dir,args.cache_dir)
    if args.self_test:
        root.update()
        app.orientation.set('Trame brute')
        app.render()
        root.update()
        app.orientation.set('Paysage D578')
        app.render()
        root.update()
        assert app.frame_image.width()>0 and app.frame_image.height()>0
        assert app.start_button.winfo_ismapped()
        assert app.save_button.winfo_ismapped()
        print(json.dumps(dict(window=[root.winfo_width(),root.winfo_height()],
                              lcd=[app.frame_image.width(),app.frame_image.height()],
                              controls_visible=True)))
        root.destroy()
    else:
        root.mainloop()


if __name__=='__main__':
    main()
