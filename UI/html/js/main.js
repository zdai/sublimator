
/* actions on startup */
window.imgTimer=null;
window.curveTimer=null;
window.imgUpdate
$(document).ready(function(){
	window.server = new serverAPI();
	
	var chartIDs=['#temp_n_vacuum'];
	var chartArgs=[];
	chartArgs.push({
		chartTitle:"Current Density (log) vs. Voltage",
		yType:"logarithmic",
		xType:"linear",
		xTitle:"Voltage(V)",
		yTitle:"Current Density(mA/cm2)",
		yMaxID:null,
		yTick:null
	});
	var legend='#legendList';
	window.chartManager = new chartManager(legend,chartIDs,chartArgs);

	window.tcScheduler 	= new tempCtrlSchedule('tempSchTable','tempCtrlId');
	var tcBlocks=[];
	for(var i=0;i<3;i++){
		var tcBlock = new tempCtrlBlock('controlPanel',i);
		tcBlocks.push(tcBlock);
	}

	//window.setInterval(run,3000);
});

function run(){
	window.server.post({'action':'get_status'},update_status);
}

function update_status(state){
}

/***************************************************************************
* second part: action processing using jquery and ajax
****************************************************************************/

/* control the plate operation menu */
$(document).ready(function(){
	$('#tempCtrlSch').hide();
	$('#tempSchAdd').click(function(){
		window.tcScheduler.addRow();
	});

	$('#tempSchCancel').click(function(){
		$('#tempCtrlSch').hide();
	});
});


/***************************************************************************
* class		: tempCtrlBlock
* purpose	: to allow generation of any number of temperature controller 
*			  on the page
****************************************************************************/
function tempCtrlBlock(pannel, id){
	this.headerId =id;
	this.parentId =pannel;
	this.init();
}

tempCtrlBlock.prototype.init=function (){
	// header
	var header=document.createElement('h3');
	header.innerHTML='Temperature Controller ' + this.headerId;

	// TC display 
	var ctrlDisp=document.createElement('table');
	ctrlDisp.setAttribute('class','tempCtrlDisp');

	// ---TC display PV
	var trPV=document.createElement('tr');
	var thPV=document.createElement('td');
	thPV.innerHTML='Process Value (<sup>o</sup>C)';
	var tdPV=document.createElement('td');
	tdPV.innerHTML=':';
	var tdPVSpan=document.createElement('span');
	tdPVSpan.setAttribute('class','tempPV');
	tdPVSpan.setAttribute('id','tempPV'+this.headerId);
	tdPVSpan.innerHTML="24.5";
	tdPV.appendChild(tdPVSpan);
	trPV.appendChild(thPV);
	trPV.appendChild(tdPV);
	
	// ---TC display SV
	var trSV=document.createElement('tr');
	var thSV=document.createElement('td');
	thSV.innerHTML='Set Value (<sup>o</sup>C)';
	var tdSV=document.createElement('td');
	tdSV.innerHTML=':';
	var tdSVSpan=document.createElement('span');
	tdSVSpan.setAttribute('class','tempSV');
	tdSVSpan.setAttribute('id','tempSV'+this.headerId);
	tdSVSpan.innerHTML="105.5";
	tdSV.appendChild(tdSVSpan);
	trSV.appendChild(thSV);
	trSV.appendChild(tdSV);

	// ---TC display pwr 
	var trPwr=document.createElement('tr');
	var thPwr=document.createElement('td');
	thPwr.innerHTML='Power Output';
	var tdPwr=document.createElement('td');
	tdPwr.innerHTML=':';
	var tdPwrSpan=document.createElement('span');
	tdPwrSpan.setAttribute('class','tempPwr');
	tdPwrSpan.setAttribute('id','tempPwr'+this.headerId);
	tdPwrSpan.innerHTML="80";
	tdPwr.appendChild(tdPwrSpan);
	trPwr.appendChild(thPwr);
	trPwr.appendChild(tdPwr);
	ctrlDisp.appendChild(trPV);
	ctrlDisp.appendChild(trSV);
	ctrlDisp.appendChild(trPwr);

	// TC setting Mode 
	var setting =document.createElement('div');
	setting.setAttribute('id','tempSetting');
	var manual =document.createElement('input');
	manual.setAttribute('type','radio');
	manual.setAttribute('value',this.headerId);
	manual.setAttribute('name','tempMode'+this.headerId);
	manual.setAttribute('id','tempManualMode'+this.headerId);
	manual.onclick=function(){setTcMode($(this).val(),'M');};
	var manualText =document.createTextNode('Manual');
	var auto =document.createElement('input');
	auto.setAttribute('type','radio');
	auto.setAttribute('value',this.headerId);
	auto.setAttribute('name','tempMode'+this.headerId);
	auto.setAttribute('id','tempAutoMode'+this.headerId);
	auto.onclick=function(){setTcMode($(this).val(),'A');};
	var autoText =document.createTextNode('Auto');

	// ----manual Mode 
	var autoCtrl =document.createElement('div');
	autoCtrl.setAttribute('id','tempAutoCtrl'+this.headerId);
	autoCtrl.setAttribute('class','tempModeCtrl');
	autoCtrl.innerHTML="Target(<sup>o</sup>C):";
	var setTgt =document.createElement('input');
	setTgt.setAttribute('type','input');
	setTgt.setAttribute('class','tempCtrlIn');
	setTgt.setAttribute('id','tempSetTgt'+this.headerId);
	var tgtBtn =document.createElement('button');
	tgtBtn.setAttribute('type','button');
	tgtBtn.setAttribute('class','tempCtrlBtn');
	tgtBtn.setAttribute('id','tempTgtBtn'+this.headerId);
	tgtBtn.innerHTML="Set";
	autoCtrl.appendChild(setTgt);
	autoCtrl.appendChild(tgtBtn);

	// ----auto Mode 
	var manualCtrl =document.createElement('div');
	manualCtrl.setAttribute('id','tempManualCtrl'+this.headerId);
	manualCtrl.setAttribute('class','tempModeCtrl');
	manualCtrl.innerHTML="Power(%):";
	var setPwr =document.createElement('input');
	setPwr.setAttribute('type','input');
	setPwr.setAttribute('class','tempCtrlIn');
	setPwr.setAttribute('id','tempSetPwr'+this.headerId);
	var pwrBtn =document.createElement('button');
	pwrBtn.setAttribute('type','button');
	pwrBtn.setAttribute('class','tempCtrlBtn');
	pwrBtn.setAttribute('id','tempPwrBtn'+this.headerId);
	pwrBtn.innerHTML="Set";
	manualCtrl.appendChild(setPwr);
	manualCtrl.appendChild(pwrBtn);

	setting.appendChild(auto);
	setting.appendChild(autoText);
	setting.appendChild(manual);
	setting.appendChild(manualText);
	setting.appendChild(manualCtrl);
	setting.appendChild(autoCtrl);

	// TC scheduler button 
	var schBtn =document.createElement('button');
	schBtn.innerHTML="Schedule";
	schBtn.setAttribute('type','button');
	schBtn.setAttribute('value',this.headerId);
	schBtn.setAttribute('id','tempSchBtn'+this.headerId);
	schBtn.setAttribute('class','tempCtrlBtn');
	schBtn.onclick=function(){
		window.tcScheduler.init($(this).val());
		$('#tempCtrlSch').show();
		};

	// TC block 
	var tcBlock=document.createElement('div');
	tcBlock.setAttribute('class','tempCtrlBlock');
	tcBlock.appendChild(header);
	tcBlock.appendChild(header);
	tcBlock.appendChild(ctrlDisp);
	tcBlock.appendChild(setting);
	tcBlock.appendChild(schBtn);
	document.getElementById(this.parentId).appendChild(tcBlock);

	// initial display 
	$('#tempAutoMode'+this.headerId).click();
};

function setTcMode(id,mode){
	if(mode == 'M'){
		$('#tempManualCtrl'+id).show();
		$('#tempAutoCtrl'+id).hide();
	}
	else if(mode == 'A'){
		$('#tempManualCtrl'+id).hide();
		$('#tempAutoCtrl'+id).show();
	}
};
/***************************************************************************
* class		: tempCtrlSchedule 
* purpose	: scheduler for multi-stage temperature controll
****************************************************************************/
function tempCtrlSchedule(tempCtrl,header){
	this.tempCtrlId=tempCtrl;
	this.headerId = header;
	this.controller=0;
	this.nRow=0;
	this.targets=[];
	this.schedules=[];
}

tempCtrlSchedule.prototype.init=function(ctrl){
	this.controller=ctrl;
	this.nRow=0;
	this.targets=[];
	this.schedules=[];
	$('#'+this.tempCtrlId).empty();
	$('#'+this.headerId).text(ctrl);
	this.addRow();
};

tempCtrlSchedule.prototype.addRow=function(){
	var row=document.createElement('tr');
	var tdTgt=document.createElement('td');
	tdTgt.innerHTML='Target(<sup>o</sup>C):';

	var tdTgtValue=document.createElement('td');
	var tgtInput=document.createElement('input');	
	tgtInput.setAttribute('class','tempSchTgt');
	tgtInput.setAttribute('id','schTgtIn'+this.nRow);
	tdTgtValue.appendChild(tgtInput);

	var tdTime=document.createElement('td');
	tdTime.innerHTML='Time:';

	var tdTimeValue=document.createElement('td');
	var timeInput=document.createElement('input');	
	timeInput.setAttribute('class','tempSchTime');
	timeInput.setAttribute('id','schTimeIn'+this.nRow);
	tdTimeValue.appendChild(timeInput);

	row.appendChild(tdTgt);
	row.appendChild(tdTgtValue);
	row.appendChild(tdTime);
	row.appendChild(tdTimeValue);
	document.getElementById(this.tempCtrlId).appendChild(row);
};

