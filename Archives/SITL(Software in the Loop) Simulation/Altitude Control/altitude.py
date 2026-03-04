"""
PyQt5 Mission Control App (layout adjusted)
- Status group shorter in height (occupies less vertical space).
- Mission and Status groups now wider (increased width column).
- Map group still covers combined height of Mission + Status.
- Telemetry plots stacked below as before.
- Bottom note included.
"""

import sys, socket, struct, threading, time
from collections import deque
import numpy as np
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

HOST='127.0.0.1'; SEND_PORT=55000; RECV_PORT=55001; TELEM_LEN=13
PLOT_INTERVAL_MS=200; SEND_HZ=10

class TelemetryReceiver(QtCore.QObject):
    telemetry_updated=pyqtSignal(object); recv_status=pyqtSignal(bool)
    def __init__(self,host,port): super().__init__(); self.host=host; self.port=port; self.running=False; self.sock=None
    def start(self):
        if self.running:return
        self.running=True; threading.Thread(target=self._run,daemon=True).start()
    def stop(self):
        self.running=False
        if self.sock:
            try:self.sock.close()
            except:pass
    def _run(self):
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM); s.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        s.bind((self.host,self.port)); s.listen(1); self.recv_status.emit(False)
        try:
            conn,addr=s.accept(); conn.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1); self.sock=conn; self.recv_status.emit(True)
            while self.running:
                data=conn.recv(8*TELEM_LEN)
                if len(data)<8*TELEM_LEN: continue
                self.telemetry_updated.emit(struct.unpack('>13d',data))
        except:
            self.recv_status.emit(False)
        finally:
            self.recv_status.emit(False); s.close(); self.running=False

class CommandSender(QtCore.QObject):
    send_status=pyqtSignal(bool)
    def __init__(self,host,port): super().__init__(); self.host=host; self.port=port; self.running=False; self.sock=None; self.command_lock=threading.Lock(); self.current_alt=0; self.mode=1
    def start(self):
        if self.running:return
        self.running=True; threading.Thread(target=self._run,daemon=True).start()
    def stop(self):
        self.running=False
        if self.sock:
            try:self.sock.close()
            except:pass
    def set_altitude(self,alt):
        with self.command_lock:self.current_alt=float(alt)
    def get_command(self):
        with self.command_lock:return(self.mode,self.current_alt)
    def _run(self):
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM); s.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1); s.bind((self.host,self.port)); s.listen(1); self.send_status.emit(False)
        try:
            conn,addr=s.accept(); conn.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1); self.sock=conn; self.send_status.emit(True)
            next_t=time.perf_counter(); dt=1.0/SEND_HZ
            while self.running:
                m,a=self.get_command(); conn.sendall(struct.pack('>2d',m,a)); next_t+=dt; d=next_t-time.perf_counter(); time.sleep(d if d>0 else 0)
        except:
            self.send_status.emit(False)
        finally:
            self.send_status.emit(False); s.close(); self.running=False

class MissionController(QtCore.QObject):
    mission_finished=pyqtSignal(); mission_started=pyqtSignal()
    def __init__(self,sender): super().__init__(); self.sender=sender; self.mission=[]; self.active=False; self.latest_telemetry=None
    def update_telemetry(self,t): self.latest_telemetry=t
    def load_mission(self,m): self.mission=m[:]
    def start(self):
        if self.active:return
        self.active=True; threading.Thread(target=self._run,daemon=True).start(); self.mission_started.emit()
    def stop(self): self.active=False
    def _run(self):
        try:
            for alt,hold,tol in self.mission:
                if not self.active:break
                self.sender.set_altitude(alt); reached=False; t0=None
                while not reached and self.active:
                    if not self.latest_telemetry: time.sleep(0.05); continue
                    tt=self.latest_telemetry[0]; z=self.latest_telemetry[3]
                    if abs(z-alt)<=tol:
                        if t0 is None:t0=tt
                        if tt-t0>=hold:reached=True
                    else:t0=None
                    time.sleep(0.05)
            if self.active:
                cur=self.sender.current_alt
                for s in np.linspace(cur,0,10):
                    if not self.active:break
                    self.sender.set_altitude(s); time.sleep(0.5)
        finally:
            self.active=False; self.mission_finished.emit()

class MplCanvas(FigureCanvas):
    def __init__(self,w=4,h=3,dpi=100):
        fig=Figure(figsize=(w,h),dpi=dpi); super().__init__(fig); self.axes=fig.subplots(); fig.tight_layout()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle('Mission Control'); self.resize(1400,1050)
        self.receiver=TelemetryReceiver(HOST,RECV_PORT); self.sender=CommandSender(HOST,SEND_PORT); self.mission_ctrl=MissionController(self.sender)
        self.receiver.telemetry_updated.connect(self.on_telemetry); self.receiver.recv_status.connect(self.on_recv_status); self.sender.send_status.connect(self.on_send_status)
        self.mission_ctrl.mission_finished.connect(self.on_mission_finished); self.mission_ctrl.mission_started.connect(self.on_mission_started)
        self._buffers(); self._build_ui(); self.receiver.start(); self.sender.start()
        self.timer=QtCore.QTimer(); self.timer.setInterval(PLOT_INTERVAL_MS); self.timer.timeout.connect(self.update_plots); self.timer.start()

    def _buffers(self):
        self.time_buf,self.x_buf,self.y_buf,self.z_buf=deque(maxlen=1000),deque(maxlen=1000),deque(maxlen=1000),deque(maxlen=1000)
        self.vx_buf,self.vy_buf,self.vz_buf=deque(maxlen=1000),deque(maxlen=1000),deque(maxlen=1000)
        self.roll_buf,self.pitch_buf,self.yaw_buf=deque(maxlen=1000),deque(maxlen=1000),deque(maxlen=1000)
        self.wx_buf,self.wy_buf,self.wz_buf=deque(maxlen=1000),deque(maxlen=1000),deque(maxlen=1000)

    def _build_ui(self):
        central=QWidget(); root=QVBoxLayout(); central.setLayout(root); self.setCentralWidget(central)

        # Upper layout: left column (Mission + small Status stacked) and right column (Map)
        upper=QHBoxLayout()
        left_col=QVBoxLayout()

        mission_box=QGroupBox('Mission'); mv=QVBoxLayout(); mission_box.setLayout(mv)
        self.mission_table=QTableWidget(0,3)
        self.mission_table.setHorizontalHeaderLabels(['Height (m)','Hold (s)','Tolerance (m)'])
        self.mission_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        mv.addWidget(self.mission_table)
        hb=QHBoxLayout(); addb=QPushButton('Add'); addb.clicked.connect(self.add_mission_row); rem=QPushButton('Remove Selected'); rem.clicked.connect(self.remove_selected_rows); hb.addWidget(addb); hb.addWidget(rem); mv.addLayout(hb)
        self.start_btn=QPushButton('Start'); self.start_btn.setCheckable(True); self.start_btn.clicked.connect(self.on_start_clicked); mv.addWidget(self.start_btn)
        left_col.addWidget(mission_box,3)

        status_box=QGroupBox('Status'); sv=QHBoxLayout(); status_box.setLayout(sv)
        self.recv_label=QLabel('RECV: Disconnected'); self.send_label=QLabel('SEND: Disconnected')
        sv.addWidget(self.recv_label); sv.addWidget(self.send_label)
        left_col.addWidget(status_box,1)

        upper.addLayout(left_col,3)  # Increased width of mission+status column

        map_box=QGroupBox('Map'); mapv=QVBoxLayout(); map_box.setLayout(mapv); self.map_canvas=MplCanvas(6,5); mapv.addWidget(self.map_canvas)
        upper.addWidget(map_box,4)

        root.addLayout(upper)

        # Lower telemetry plots stacked
        self.vel_canvas=MplCanvas(); self.orient_canvas=MplCanvas(); self.angvel_canvas=MplCanvas()
        root.addWidget(self._group_wrap('Velocities',self.vel_canvas))
        root.addWidget(self._group_wrap('Orientation',self.orient_canvas))
        root.addWidget(self._group_wrap('Angular Velocities',self.angvel_canvas))

        note=QLabel('Telemetry format: [time, x, y, z, vx, vy, vz, roll, pitch, yaw, wx, wy, wz]')
        note.setAlignment(Qt.AlignCenter); root.addWidget(note)

    def _group_wrap(self,title,canvas):
        g=QGroupBox(title); v=QVBoxLayout(); v.addWidget(canvas); g.setLayout(v); return g

    def add_mission_row(self):
        r=self.mission_table.rowCount(); self.mission_table.insertRow(r)
        self.mission_table.setItem(r,0,QTableWidgetItem('1.0'))
        self.mission_table.setItem(r,1,QTableWidgetItem('5.0'))
        self.mission_table.setItem(r,2,QTableWidgetItem('0.5'))

    def remove_selected_rows(self):
        for r in sorted({i.row() for i in self.mission_table.selectedIndexes()},reverse=True): self.mission_table.removeRow(r)

    def on_start_clicked(self,chk):
        if chk:
            mission=[]
            for r in range(self.mission_table.rowCount()):
                try:
                    alt=float(self.mission_table.item(r,0).text()); hold=float(self.mission_table.item(r,1).text()); tol=float(self.mission_table.item(r,2).text()); mission.append((alt,hold,tol))
                except: QMessageBox.warning(self,'Invalid',f'Invalid row {r+1}'); self.start_btn.setChecked(False); return
            if not mission: QMessageBox.warning(self,'Empty','Add at least one mission'); self.start_btn.setChecked(False); return
            self.mission_table.setEnabled(False); self.start_btn.setText('Stop'); self.mission_ctrl.load_mission(mission); self.mission_ctrl.start()
        else:
            self.mission_ctrl.stop(); self.mission_table.setEnabled(True); self.start_btn.setText('Start')

    def on_recv_status(self,c): self.recv_label.setText('RECV: Connected' if c else 'RECV: Disconnected')
    def on_send_status(self,c): self.send_label.setText('SEND: Connected' if c else 'SEND: Disconnected')
    def on_mission_finished(self): self.start_btn.setChecked(False); self.start_btn.setText('Start'); self.mission_table.setEnabled(True)
    def on_mission_started(self): pass

    def on_telemetry(self,t):
        tt,x,y,z,vx,vy,vz,roll,pitch,yaw,wx,wy,wz=t
        self.time_buf.append(tt); self.x_buf.append(x); self.y_buf.append(y); self.z_buf.append(z)
        self.vx_buf.append(vx); self.vy_buf.append(vy); self.vz_buf.append(vz)
        self.roll_buf.append(roll); self.pitch_buf.append(pitch); self.yaw_buf.append(yaw)
        self.wx_buf.append(wx); self.wy_buf.append(wy); self.wz_buf.append(wz)
        self.mission_ctrl.update_telemetry(t)

    def update_plots(self):
        ax=self.map_canvas.axes; ax.clear()
        if self.x_buf:
            ax.plot(self.x_buf,self.y_buf); ax.scatter(self.x_buf[-1],self.y_buf[-1]);
            ax.text(0.98,0.98,f'X={self.x_buf[-1]:.2f}\nY={self.y_buf[-1]:.2f}\nZ={self.z_buf[-1]:.2f}',transform=ax.transAxes,ha='right',va='top',bbox=dict(boxstyle='round',alpha=0.6));
            ax.set_xlabel('X'); ax.set_ylabel('Y')
        self.map_canvas.draw()
        self._simple_plot(self.vel_canvas.axes,self.time_buf,[self.vx_buf,self.vy_buf,self.vz_buf],['vx','vy','vz'],'Velocities')
        self._simple_plot(self.orient_canvas.axes,self.time_buf,[self.roll_buf,self.pitch_buf,self.yaw_buf],['roll','pitch','yaw'],'Orientation')
        self._simple_plot(self.angvel_canvas.axes,self.time_buf,[self.wx_buf,self.wy_buf,self.wz_buf],['wx','wy','wz'],'Angular Velocities')

    def _simple_plot(self,ax,t,ys,labels,title):
        ax.clear()
        if t:
            for y,l in zip(ys,labels): ax.plot(t,y,label=l)
            ax.legend(); ax.set_xlabel('Time'); ax.set_title(title)
        if title=='Velocities': self.vel_canvas.draw()
        elif title=='Orientation': self.orient_canvas.draw()
        else: self.angvel_canvas.draw()

    def closeEvent(self,e): self.receiver.stop(); self.sender.stop(); self.mission_ctrl.stop(); e.accept()

def main(): app=QApplication(sys.argv); w=MainWindow(); w.show(); sys.exit(app.exec_())
if __name__=='__main__': main()