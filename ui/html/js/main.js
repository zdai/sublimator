
/* actions on startup */
window.curveTimer=null;
$(document).ready(function(){
	window.server = new serverAPI();

	var yAxises=[];
	yAxises.push({
		format:'{value}°C',
		formatter:null,
		title:'temperature',
		type:'linear',
		opposite:false
		});
	yAxises.push({
		format:'{value} Pa',
		formatter:function(){return this.value.toExponential(1)},
		title:'vacuum',
		type:'logarithmic',
		opposite:true
		});

	var chartArgs={
		chartTitle:"Temperature and Vacuum over Time",
		xType:"linear",
		xTitle:"time",
		yAxis:yAxises,
		yMaxCtrl:null
		};
	var chartIDs='#temp_n_vacuum';
	window.chartInst = new multiYaxisChart(chartIDs,chartArgs);

	window.tcScheduler 	= new tempCtrlSchedule('tempCtrlSch','tempSchTable','tempCtrlId');
	window.tcBlocks=[];
	for(var i=0;i<3;i++){
		var tcBlock = new tempCtrlBlock('controlPanel',i);
		window.tcBlocks.push(tcBlock);
	}

	window.setInterval(run,3000);
	run(); //run for the first time

});

function run(){
	window.server.post({'action':'get_status'},update_status);
	window.server.post({'action':'get_chart'},update_chart);
}

function update_status(state){
	var pvArray	=state.temp_pv;
	var svArray	=state.temp_sv;
	var pwrArray=state.temp_pwr;
	var modes	=state.temp_mode;
	for(var i=0;i<window.tcBlocks.length;i++){
		window.tcBlocks[i].update(pvArray[i],svArray[i],pwrArray[i],modes[i]);
	}

	//var vcReading=state.vacuum[0]+'.'+state.vacuum[1]+'E'+state.vacuum.substring(2,4);
	var vcReading=parseFloat(state.vacuum).toExponential(1);
	$('#vacuumReading').text(vcReading);
	$('#processLabel').text(state.label);
	$('#elapseTime').text(state.elapse);
}

function update_chart(raw){
	var vacuum 	=raw.vacuum;
	var tempArr	=raw.temps;
	var time	=raw.time;

	window.chartInst.setXcategory(time);

	window.chartInst.appendSeries('vacuum',vacuum,1);	

	for(var i=0;i<tempArr.length;i++)
		window.chartInst.appendSeries('TC'+i,tempArr[i],0);	

	window.chartInst.drawChart();
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

tempCtrlBlock.prototype.update=function (pv,sv,pwr,mode){
	$('#tempPV'+this.headerId).text(pv);
	if(mode == 'M'){
		$('#tempSV'+this.headerId).text('__ __');
		$('#tempManualMode'+this.headerId).click();
	}
	else if(mode == 'A'){
		$('#tempSV'+this.headerId).text(sv);
		$('#tempAutoMode'+this.headerId).click();
	}
	$('#tempPwr'+this.headerId).text(pwr);
};
/***************************************************************************
* class		: tempCtrlSchedule 
* purpose	: scheduler for multi-stage temperature controll
****************************************************************************/
function tempCtrlSchedule(parentCtrl,tempCtrl,header){
	this.parentCtrl=parentCtrl;
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
	var leftOffset=380+367*parseInt(ctrl);
	var leftPx =leftOffset.toString()+'px';
	$('#'+this.parentCtrl).css('left',leftPx);
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

/***************************************************************************
* line chart instance class
****************************************************************************/
function multiYaxisChart(id,args){
	this.chartID=id;

	this.chartTitle="";
	this.xAxis={
		title:"",
		categories:[],
		type:"linear"
	};

	this.yAxis=[];
	this.legend={
		layout:'vertical',
        align: 'left',
		verticalAlign:'top',
		floating:true,
		x:70,
		y:30,
		margin:0,
		padding:0,
		enabled:true
	};

	this.series=[];

	this.sColor=["#7cb5ec","#434348","#90ed7d","#f7a35c","#8085e9",
				"#f15c80","#e4d354","#2b908f","#f45b5b","#91e8e1",
				"#007897"];
	this.mSymbol=['circle','triangle','diamond','square','triangle-down'];

	this.legendCnt = 0;
	this.setup(args);
}

// setup x and y axis
multiYaxisChart.prototype.setup=function(args){
	if(args.xAxisCtrl)
		this.xAxisCtrl=args.xAxisCtrl;

	this.yMaxCtrl=args.yMaxCtrl;
	this.chartTitle=args.chartTitle;
	this.setXAxis(args.xTitle,args.xType);

	var yAxis=args.yAxis;
	for(var i=0;i<yAxis.length;i++)
		this.addYAxis(yAxis[i].format,yAxis[i].formatter,yAxis[i].title,yAxis[i].type,yAxis[i].opposite);

	this.series=[];
	if(args.mouse != null)
		this.mouseTracking = args.mouse;
	else
		this.mouseTracking = true;
};

multiYaxisChart.prototype.setXAxis=function(title,type){
	this.xAxis.title=title;
	this.xAxis.type=type;
};

multiYaxisChart.prototype.addYAxis=function(labelFormat,labelFormatter,title,type,opposite){
	var index=this.yAxis.length;
	var newAxis={
		labels:{
			format:labelFormat,
			formatter:labelFormatter,
			style:{
				color:this.sColor[this.index%this.sColor.length]
			}
		},
		title:{
			text:title,
			style:{
				color:this.sColor[this.index%this.sColor.length]
			}
		},
		type:type,
		opposite:opposite
		};
	this.yAxis.push(newAxis);
};

// check if the specified data series already in the list 
multiYaxisChart.prototype.getLabelID=function(label){
	for(var i=0;i<this.series.length;i++)
		if(this.series[i].name == label)
			return i;
	return -1;
};

// get the setting of next legend symbol
multiYaxisChart.prototype.getNextLegend=function(){
	var legend={};
	legend.color =this.sColor [this.legendCnt % this.sColor.length ];
	legend.symbol=this.mSymbol[this.legendCnt % this.mSymbol.length];
	legend.fill  =this.sColor [this.legendCnt % this.sColor.length ];
	if(parseInt(this.series.length/this.mSymbol.length+0.9)%2)
		legend.fill='#FFFFFF';

	return legend;
};

multiYaxisChart.prototype.setXcategory=function(xCategory){
	this.xAxis.categories=xCategory;
};

// add new data series to the list 
multiYaxisChart.prototype.appendSeries=function(label,data,yAxis){
	if(label == null || label.length == 0)
		return;

	var index = this.getLabelID(label);
	if (index == -1){
		var legend=this.getNextLegend();
		newSeries={
			name:label,
			data:data,
			color:legend.color,
			enableMouseTracking:this.mouseTracking,
			yAxis:yAxis,
			marker:{
				lineColor:null,
				lineWidth:1,
				fillColor:legend.fill,
				symbol:legend.symbol
			}
		};
		this.series.push(newSeries);
		this.legendCnt += 1;
	}
	else{ // if already exist, update the data 
		this.series[index].data=data;
	}
};

// draw the line chart 
multiYaxisChart.prototype.drawChart=function(){
	var drawSeries=[];
	var yMax=null;
	if(this.yMaxCtrl != null)
		yMax=$(this.yMaxCtrl).val();

	if(this.xAxisCtrl)
		this.xAxis.type=$(this.xAxisCtrl).val();

	var chart={
		chart:{
			backgroundColor:'#FFFEF0',
			type:'spline'
		},
        title:{text: this.chartTitle},
		plotOptions: {
            series: {
                animation: false
            }
        },
		xAxis:{
			title:{text:this.xAxis.title},
			type:this.xAxis.type,
			categories:this.xAxis.categories
		},
        yAxis:this.yAxis,
        legend:this.legend,
        series:this.series
    };
	$(this.chartID).highcharts(chart);
};

