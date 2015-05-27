# The AutoTesterInterface connects to the autotester
# control boards and can be used to control the autotester.
from autoTesterHardware import AutoTesterObject, AutoTesterHardware
from mongo_agent import MongoAgent
from oledAgeTest import *
from log_console import *

import math, threading, Queue
from datetime import datetime, timedelta
import os, sys, json
import cv2, base64
import ConfigParser

class AutoTesterInterface(AutoTesterObject):
	def __init__(self,cfg="ini/autotester.cfg"):
		"""
		   program control parameters
		"""
		self.console=LogConsole("logs/autotester.log",pts=True,buf_size=32)
		self.cfg_file=cfg
		self.config=ConfigParser.ConfigParser()
		self.load_cfg_file(self.cfg_file)
		self._setup()

		# database agent to store and retrieve data
		self.database=MongoAgent(self.console,self.config)
		self.abort_all=False
		self.skip_dev=False
		self.state="IDLE"

		# all the mechanic part control
		self.hardware=AutoTesterHardware(self.config)
		self.agingTest=OledAgingTest(self.console,self.config,self.hardware,self.database)

		"""
		   actions at system power up
		"""
		self._chip_init()
		self.hardware.reset()

	def load_cfg_file(self,cfg):
		try:
			self.console.log("Reading autotester configuration file {}..."
										  .format(cfg))
			self.config.read(cfg)
		except Exception as e:
			self.console.log ("[failed!]{}\n".format(e))
			return None
		finally:
			self.console.log("[done!]\n")
			self._setup()
			return json.dumps(self.config.__dict__['_sections'])

	def save_cfg_file(self,cfg,opts):
		for session in opts:
			for option in opts[session]:
				try:
					self.config.set(session,option,opts[session][option])
				except Exception as e:
					return ("failed!{}".format(e))

		with open(cfg,'w+') as cfg_file:
			self.config.write(cfg_file)

		return ('configuration saved to file %s' % cfg)

	def _setup(self):
		"""
			platform control parameters
		"""
		self.debug=self.config.getboolean("APP","debug")
		self.examine_volt=self.config.getfloat("MULTIMETER","exam_volt")#voltage for device examination
		self.examine_curr_range={
			'low':self.config.getfloat("MULTIMETER","exam_curr_low"),
			'high':self.config.getfloat("MULTIMETER","exam_curr_high")}

		 #activate the camera when the voltage fall into the range
		self.camera_window={
			'start':self.config.getfloat("WEBCAM","start_volt"),
			'stop':self.config.getfloat("WEBCAM","stop_volt")}

		"""
			test chip description parameters
		"""
		self.current_chip=self.config.get("CHIP","default_label") #set default chip label
		self.dev_range={
			'x':self.config.getint("CHIP","num_of_col"),
			'y':self.config.getint("CHIP","num_of_row")} #set default chip layout
		w=self.config.getfloat("DEVICE","width")
		l=self.config.getfloat("DEVICE","length")
		self.dev_width=[w for _ in range(self.dev_range['x']*self.dev_range['y'])]
		self.dev_length=[l for _ in range(self.dev_range['x']*self.dev_range['y'])]
		self.dev_area=[(w*l) for _ in range(self.dev_range['x']*self.dev_range['y'])]
		self.auto_save_dir=self.config.get("APP","save_path")


	"""
	 Mango DB operations
	 - store and retrieve chip, device and test data
	"""
	def _update_device_info(self,x,y,dev_idx):
		if not self.database:
			return False

		# if not exist, the update will do an insert
		self.database.update_device(
						chip		=self.current_chip,
						cor_x		=x,
						cor_y		=y,
						width		=self.dev_width[dev_idx],
						length		=self.dev_length[dev_idx],
						test_times	=self.dev_tests[dev_idx],
						status		=self.dev_status[dev_idx]
						)

	def get_chip_status(self,chip_label):
		if not self.database:
			return None
		return self.database.get_chip_status(chip_label)

	def register_chip(self,args):
		if not self.database:
			return False

		label=args['label']
		note=''
		if 'note' in args:
			note = args['note']

		nrow = self.config.getint("CHIP","num_of_row")
		ncol = self.config.getint("CHIP","num_of_col")
		nlayer = 0
		if 'nrow' in args:
			nrow = args['nrow']
		if 'ncol' in args:
			ncol = args['ncol']
		if 'nlayer' in args:
			nlayer = args['nlayer']

		time=datetime.now()
		return self.database.insert_chip(reg_time=time,label=label,
				nlayer=nlayer,nrow=nrow,ncol=ncol,note=note)

	def get_device_list(self,chip_label):
		if not self.database:
			return None

		chip_status=self.database.get_chip_status(chip_label)
		dev_list=[]
		dev_id=[]
		if not chip_status == None:
			dev_status = chip_status['dev_status']
			for i, v in enumerate(dev_status):
				if v:
					dev_list.append('Dev'+'%02d'%i)

		return {'devices':dev_list, 'chip':chip_label}

	def get_device_tests(self,label):
		if not self.database:
			return None

		tests=self.database.get_device_tests(label)
		return {'label':label,'tests':tests}

	def get_test_info(self,label,series):
		if not self.database:
			return None

		tests=self.database.get_eff_test(label,series)
		tests['label'] = label+'-'+series
		return tests

	def get_test_img(self,label):
		if not self.database:
			return None
		imgs=self.database.get_test_img(label)
		return imgs

	def get_spectrum(self,label):
		if not self.database:
			return None
		spectrum = self.database.get_spectrum(label)
		return spectrum

	"""
	 parameter set and get
	 - set device area, select device, chip status, test data etc.
	 - get physical location of a device
	 - validate the index of a device
	"""
	def _chip_init(self):
		self.dev_selected = {'x':0,'y':0}
		self.dev_tests  =[0  for _ in range(self.dev_range['x']*self.dev_range['y'])]
		self.dev_status =[0  for _ in range(self.dev_range['x']*self.dev_range['y'])]
		self.stamp      =['' for _ in range(self.dev_range['x']*self.dev_range['y'])]
		self.volt       =[[] for _ in range(self.dev_range['x']*self.dev_range['y'])]
		self.curr       =[[] for _ in range(self.dev_range['x']*self.dev_range['y'])]
		self.lumi       =[[] for _ in range(self.dev_range['x']*self.dev_range['y'])]
		self.CD         =[[] for _ in range(self.dev_range['x']*self.dev_range['y'])]
		self.CE         =[[] for _ in range(self.dev_range['x']*self.dev_range['y'])]
		self.PE         =[[] for _ in range(self.dev_range['x']*self.dev_range['y'])]
		self.EQE        =[[] for _ in range(self.dev_range['x']*self.dev_range['y'])]
		self.pic        =[[] for _ in range(self.dev_range['x']*self.dev_range['y'])]
		self.spectrum 	=[[] for _ in range(self.dev_range['x']*self.dev_range['y'])]

	def set_curr_chip(self,chip_label):
		if self.state == "Testing":
			return False

		chip_status=self.get_chip_status(chip_label)
		if chip_status==None:
			return False

		self.current_chip	=chip_label
		self.dev_range['x']	=chip_status['chip']['col']
		self.dev_range['y']	=chip_status['chip']['row']
		self._chip_init()

		for x in range(self.dev_range['x']):
			for y in range(self.dev_range['y']):
				idx=y*self.dev_range['x']+x
				if not chip_status['dev_info'][idx] == None:
					dev_info=chip_status['dev_info'][idx]
					self.dev_width[idx]	=float(dev_info['width'])
					self.dev_length[idx]=float(dev_info['length'])
					self.dev_area[idx]	=self.dev_width[idx]*self.dev_length[idx]
					self.dev_tests[idx]	=int(dev_info['test_times'])
		return True

	def save_motor_offset(self):
		offset=self.hardware.get_motor_offset()
		self.config.set("MOTOR","offset_x",offset['x'])
		self.config.set("MOTOR","offset_y",offset['y'])
		self.config.set("MOTOR","offset_z",offset['z'])
		with open(self.cfg_file,"w+") as cfg:
			self.config.write(cfg)

	def set_calibration(self,volt):
		if self.state == "calibration":
			self.hardware.set_source_voltage(level=volt)
			self.hardware.set_gate('ON')
			return True
		else:
			return False

	def set_dev_area(self,w,l):
		for i in range(self.dev_range['x']*self.dev_range['y']):
			self.dev_width[i]	=float(w)*1E-3
			self.dev_length[i]	=float(l)*1E-3
			self.dev_area[i]	=float(w)*float(l)* 1E-6

	def select_device(self,x,y=None):
		if not self._validate_index(x,y):
			return False
		else:
			self.dev_selected = { 'x': x, 'y': y }
			return True

	def get_webcam(self):
		return self.hardware.get_webcam()

	# delete previous measurement before storing the new results
	def _clear_measurement(self,idx):
		del self.volt[idx][:]
		del self.curr[idx][:]
		del self.lumi[idx][:]
		del self.CD[idx][:]
		del self.CE[idx][:]
		del self.PE[idx][:]
		del self.EQE[idx][:]
		del self.pic[idx][:]
		del self.spectrum[idx][:]
		self.dev_status[idx] = 0

	# current status of the test plate
	def get_status(self):
		dev_area=0.0
		if self.dev_selected != None:
			dev_idx=self.dev_selected['x'] + self.dev_selected['y']*self.dev_range['x']
		else:
			dev_idx=0
		dev_area=self.dev_area[dev_idx]

		result={
				'chip_label':self.current_chip,
				'sel_dev':self.dev_selected,
				'motor_pos':self.hardware.get_motor_position(),
				'dev_status':self.dev_status,
				'dev_area':dev_area,
				'state':self.state
				}
		return result

	def _get_lumi_spectrum(self,dev_idx,lumi):
		if not len(self.lumi[dev_idx]):
			return -1

		prev_lumi = 0
		for i,l in enumerate (self.lumi[dev_idx]):
			if lumi >= prev_lumi and lumi < l:
				return i
			prev_lumi = l

		if lumi > self.lumi[dev_idx][0]:
			return 0
		elif lumi > self.lumi[dev_idx][-1]:
			return len(self.lumi[dev_idx])

	# get current test data for the entire chip
	def get_eff_data(self,spectrum_mode,lumi,load_all):
		if self.dev_selected == None:
			return None

		dev_idx=self.dev_selected['x'] + self.dev_selected['y']*self.dev_range['x']

		spectr 		= []
		spectr_point= 0
		spectr_lumi	= 0

		if spectrum_mode == 'single_device':
			if len(self.volt[dev_idx]) > 0:
				spectr_point = self.volt[dev_idx][-1]
				spectr_lumi  = self.lumi[dev_idx][-1]

				if load_all:
					spectr=self.spectrum[dev_idx]
				else:
					spectr.append(self.spectrum[dev_idx][-1])
		else:
			index=self._get_lumi_spectrum(dev_idx,float(lumi))
			if index >= 0 and not self.hardware.spectrumeter.dummy:
				spectr.append(self.spectrum[dev_idx][index])
				spectr_point = self.volt[dev_idx][index]
				spectr_lumi	 = self.lumi[dev_idx][index]
			else:
				spectr.append(None)

		result={'volt'			:self.volt[dev_idx],
				'curr'			:self.curr[dev_idx],
				'lumi'			:self.lumi[dev_idx],
				'CD'			:self.CD[dev_idx],
				'PE'			:self.PE[dev_idx],
				'CE'			:self.CE[dev_idx],
				'EQE'			:self.EQE[dev_idx],
				'chip'			:self.current_chip,
				'device'		:'Dev%02d' % dev_idx,
				'series'		:self.stamp[dev_idx],
				'spectr_lumi'	:spectr_lumi,
				'spectr_point'	:spectr_point,
				'spectrum'		:spectr
		}

		return result

	# export all current test data to text file
	def export_test_results(self):
		if not os.path.exists(self.auto_save_dir):
			return False

		path=self.auto_save_dir+'/'+self.current_chip
		if not os.path.exists(path):
			os.mkdir(path)
		for i in range(self.dev_range['x']*self.dev_range['y']):
			if self.dev_status[i] != 0: # only store devices that have test results
				filename=path+'/Dev'+('%02d'%i)+'_eff.txt'
				with open(filename,'a+') as f:
					f.write("%s\n" % (self.stamp[i]))
					if self.dev_status[i] == -1:
						f.write("\t-pre-test: FAILED!\n")
					elif self.dev_status[i] == 2:
						f.write("\t-pre-test: PASSED!\n")
					f.write("\tVoltage(V) \t Current(uA) \t CD(mA/cm2) \t Luminance(cd/m2) \t CE(cd/A) \t PE(lm/W)\n")
					for x,v in enumerate(self.volt[i]):
						f.write("\t%8.4f \t %8.12f \t %8.4f \t %8.4f \t %8.8f \t %8.4f \n" %
								(v,float(self.curr[i][x])*1E6,self.CD[i][x],
								 self.lumi[i][x],self.CE[i][x],self.PE[i][x]))

	"""
	 motor action and measurement
	 - skip test
	 - go home
	 - move to selected device
	 - connect the device to multimeter
	 - measure IVL data
	 - auto test
	"""
	def abort_all_test(self):
		self.abort_all=True

	def skip_test(self):
		self.skip_dev=True

	def home(self):
		if self.state=="Testing":
			return False
		self.hardware.home()
		return True

	def move_to_dev(self,x=None,y=None,cb=None):
		if self.state=="Testing":
			return False

		return self.hardware.move_to_dev(x,y,cb)

	def calibrate_dev(self,args):
		if self.state != "calibration":
			return False

		self.hardware.calibrate_dev(args)
		return True

	def begin_calibration(self):
		if self.state == "Testing":
			return False

		self.hardware.set_source_voltage(level=4)
		self.hardware.set_gate('ON')
		self.state="calibration"
		self.hardware.set_focus()
		return True

	def end_calibration(self):
		if self.state != "calibration":
			return False

		self.hardware.set_gate('OFF')
		self.state="IDLE"
		return True

	# This function connects the appropriate relays to the device, so that
	# power can be applied.
	def connect_device(self,x=None,y=None):
		if self.state == "Testing":
			return False
		return self.hardware.connect_device(x,y)

	def _examine_dev(self,x=None,y=None):
		if not self._validate_index(x,y):
			return -1

		dev_idx=x+y*self.dev_range['x']
		self.hardware.set_source_voltage(level=self.examine_volt)
		self.hardware.set_gate('ON')
		time.sleep(0.5) # wait for certain time before measurement
		i=round(self.hardware.read_multimeter(),12)
		if i < self.examine_curr_range['low'] or i > self.examine_curr_range['high']:
			self.dev_status[dev_idx]=-1
			self.hardware.set_gate('OFF')

		return self.dev_status[dev_idx]

	def _efficiency_test(self,x=None,y=None,start=0,stop=15,step=0.5,delay=2.0):
		if not self._validate_index(x,y):
			return False

		dev_idx=x + y * self.dev_range['x']
		self.hardware.test_device(x,y)
		examine_fail=False
		if self._examine_dev(x,y)==-1:
			print ({"errCode":"ERR_01","logMsg":"selected device fails examination"})
			examine_fail=True

		self._clear_measurement(dev_idx)
		v=start
		self.skip_dev=False
		self.dev_status[dev_idx]=1 # measurement in progress
		self.dev_tests[dev_idx] += 1
		self.stamp[dev_idx]=('Test%02d'%self.dev_tests[dev_idx])\
			+datetime.now().strftime(" (%Y-%m-%d %H:%M)")
		self._update_device_info(x,y,dev_idx)
		stop=stop+0.1 # to ensure the test of last point

		while v < stop and self.skip_dev==False and self.abort_all==False:
			self.hardware.set_source_voltage(level=v)
			self.hardware.set_gate('ON')
			time.sleep(delay) # wait for certain time before measurement

			i=round(self.hardware.read_multimeter(),12)
			l=round(self.hardware.read_luminance(),12)

			# measure spectrum
			integ=self.hardware._get_integration_time(l)
			self.hardware.set_integration(integ)
			time.sleep((3*integ)+1)
			self.spectrum[dev_idx].append(self.hardware.get_spectrum())

			# record the results
			self.curr[dev_idx].append(i)
			self.lumi[dev_idx].append(l)
			self.volt[dev_idx].append(v)
			self.CD[dev_idx].append(round(i/self.dev_area[dev_idx]/10,12)) #mA/cm2
			if not i==0:
				self.CE[dev_idx].append(round(l*self.dev_area[dev_idx]/i,6)) #
			else:
				self.CE[dev_idx].append(0)
			if not v==0 and not i==0:
				self.PE[dev_idx].append(round(l*3.14*self.dev_area[dev_idx]/v/i,6))
			else:
				self.PE[dev_idx].append(0)

			eqe=self.hardware._calculate_eqe(l,i,self.spectrum[dev_idx][-1])
			self.EQE[dev_idx].append(eqe)
			self._store_test(dev_idx)
			self._store_spectrum(dev_idx)
			if (v > self.camera_window['start']) and (v < self.camera_window['stop']):
				self.pic[dev_idx].append(self.hardware.get_webcam())
				self._store_eff_shot(dev_idx)

			v+=step

		self.hardware.set_gate('OFF')
		if not examine_fail:
			self.dev_status[dev_idx]=2
		else:
			self.dev_status[dev_idx]=-1

	def _eff_label(self,dev_idx):
		return self.current_chip+('-Dev%02d' % dev_idx)

	def _eff_extra_label(self,dev_idx):
		label= self._eff_label(dev_idx)+'-'+self.stamp[dev_idx]
		return label

	def _store_eff_shot(self,dev_idx):
		if not self.database:
			return False

		eff_pic_label=self._eff_extra_label(dev_idx)
		self.database.insert_picture(
			test_type	='efficiency',
			label		=eff_pic_label,
			point		=self.volt[dev_idx][-1],
			pic 		=self.pic[dev_idx][-1])

	def _store_spectrum(self,dev_idx):
		if not self.database:
			return False

		spectrum_label=self._eff_extra_label(dev_idx)
		self.database.insert_spectrum(
			test_type	='efficiency',
			label		=spectrum_label,
			volt		=self.volt[dev_idx][-1],
			lumi		=self.lumi[dev_idx][-1],
			wavelength	=self.spectrum[dev_idx][-1]['wavelength'],
			intensity	=self.spectrum[dev_idx][-1]['intensity']
		)

	def _store_test(self,dev_idx):
		if not self.database:
			return False

		self.database.insert_efficiency_test(
				label		=self._eff_label(dev_idx),
				series		=self.stamp[dev_idx],
				volt		=self.volt[dev_idx][-1],
				curr		=self.curr[dev_idx][-1],
				lumi		=self.lumi[dev_idx][-1],
				ce			=self.CE[dev_idx][-1],
				cd			=self.CD[dev_idx][-1],
				pe			=self.PE[dev_idx][-1],
				eqe			=self.EQE[dev_idx][-1]
		)

	def auto_test(self,args):
		if self.state == 'Testing':
			return False

		if 'pattern' in args:
			pattern=args['pattern']
		else:
			pattern=[]

		self.abort_all = False
		self.state="Dark Calibration"
		self.hardware.dark_calibration()
		self.state="Testing"
		for index in pattern:
			if self.abort_all:
				break;

			idx=int(index % self.dev_range['x'])
			idy=int(index / self.dev_range['x'])
			self.select_device(idx,idy)
			self._efficiency_test(idx,idy,start=float(args['start']),
					stop=float(args['stop']),step=float(args['step']))

		self.state="Completed"
		self.export_test_results()

	"""
		aging test functions
	"""
	def aging_test(self,args):
		self.state="Testing"
		self.agingTest.auto_test(args)
		self.state="IDLE"

	def aging_skip_test(self):
		self.agingTest.skip_curr_dev = True

	def aging_stop_test(self):
		self.agingTest.stop = True
		self.state="IDLE"

	def get_aging_status(self):
		return self.agingTest.get_aging_status()

	def get_aging_data(self,args):
		return self.agingTest.get_aging_data(args)

	def set_aging_label(self,args):
		if 'label' in args:
			return self.agingTest.set_label(args['label'])
		else:
			return False

	def export_aging_history(self):
		self.agingTest.export_history()
		return True

	#================================================================
	# spectrumeter
	#================================================================
	def set_integration(self,seconds):
		self.hardware.set_integration(seconds)

	def get_spectrum(self):
		return self.hardware.get_spectrum()

