

/***************************************************************************
* spectrum series class
****************************************************************************/
function spectrumSeries(){
	this.series	=[];
	this.lumi	=[];
	this.points	=[];
}

spectrumSeries.prototype.append=function(data,l,p){
	for(var i=0;i<this.points.length;i++)
		if (this.points[i] == p){
			//this.series[i] = data;
			this.lumi[i] = l;
			return;
		}

	//this.series.push(data);
	this.lumi.push(l);
	this.points.push(p);
};

spectrumSeries.prototype.atPoint=function(p){
	for(var i=0;i<this.points.length;i++)
		if(this.points[i] == p)
			return this.series[i];

	return null;
};

spectrumSeries.prototype.atLumi=function(l){
	var prev=0;
	for(var i=0;i<this.points.length;i++)
		if((this.lumi[i] >= l) && (l >= prev))
			return this.series[i];
		else
			prev=this.lumi[i]
};

/***************************************************************************
* spectrum data manager class
****************************************************************************/
function spectrumManager(chartID,spectrLumi,chartArgs){
	this.mode='single_device';
	this.spectrumLumi=spectrLumi;
	this.labels=[];
	this.devices=[];
	this.series=[];
	this.chart=new chartInstance(chartID,chartArgs);
	this.currSeq=0;
}

spectrumManager.prototype.clearSeries=function(){
	this.series=[];
	this.labels=[];
	this.devices=[];
	this.currSeq=0;
	this.chart.clearSeries();
};

spectrumManager.prototype.appendSeries=function(label,dev,l,p,data,display){
	if(this.mode=='single_device'){
		if(this.labels.length > 0 && this.labels[0] != label)
			this.clearSeries();

		if(this.labels.length == 0){
			this.labels.push(new String(label));
			this.devices.push(new String(dev));
			this.series.push(new spectrumSeries());
		}

		this.series[0].append(data,l,p);
		var chartLabel=this.getSeriesLabel(this.series[0].points.length-1);
		this.chart.appendSeries(chartLabel,data,display);
	}

	else if (this.mode=='multi_device'){
		var chartLabel='';
		var exist=false;
		for(var i=0;i<this.labels.length;i++){
			if(this.labels[i] == label){
				this.series[i].append(data,l,p);
				chartLabel=this.getSeriesLabel(i);
				exist=true;
			}
		}
		if(!exist){
			this.labels.push(label);
			this.devices.push(dev);
			this.series.push(new spectrumSeries());
			var tail=this.series.length-1;
			this.series[tail].append(data,l,p);
			chartLabel=this.getSeriesLabel(tail);
		}
		this.chart.appendSeries(chartLabel,data,display);	
	}
};

spectrumManager.prototype.getSeriesLabel=function(index){
	if(this.mode == 'single_device')
		return 'V='+this.series[0].points[index].toString();
	else{
		dataSeries = this.series[index];
		return (this.devices[index])+'(L:'+dataSeries.lumi[0].toString()+')';
	}
};

spectrumManager.prototype.removeSeries=function(label){
	for(var i=0;i<this.series.length;i++){
		if (this.labels[i] == label){
			if(this.mode == 'single_device')
				for(var p=0;p<this.series[i].points.length;p++){
					var chartLabel = this.getSeriesLabel(p); 
					this.chart.removeSeries(chartLabel);
				}
			else{
				var chartLabel = this.getSeriesLabel(i);
				this.chart.removeSeries(chartLabel);
			}

			this.labels.splice(i,1);
			this.devices.splice(i,1);
			this.series.splice(i,1);
		}
	}
};

spectrumManager.prototype.checkDevice=function(dev){
	for(var i=0;i<this.devices.length;i++)
		if(this.devices[i] == dev)
			return true;

	return false;
};

spectrumManager.prototype.prevSpectrum=function(){
	if (this.currSeq > 0){
		this.currSeq -= 1;
	}
	this.setDisplay(this.currSeq);
};

spectrumManager.prototype.nextSpectrum=function(){
	if (this.series.length == 0) return;

	if (this.currSeq < this.series[0].points.length-1){
		this.currSeq += 1;
	}
	this.setDisplay(this.currSeq);
};

spectrumManager.prototype.setDisplay=function(index){
	if(this.mode == 'multi_device'){
		this.chart.chartTitle = ('Normalized Spectrum @ L closest to ' + $(this.spectrumLumi).val());
		this.chart.legend.enabled = true;
		this.chart.drawChart();
		return
	}

	this.chart.legend.enabled = false;
	if(index == -1){
		for(var p=0;p<this.series[0].points.length;p++){
			var chartLabel =  this.getSeriesLabel(p);
			this.chart.setSeriesDisplay(chartLabel,true);
		}

		this.chart.chartTitle = ('Normalized Spectrum @ All');
		this.chart.drawChart();
	}
	else{
		for(var p=0;p<this.series[0].points.length;p++){
			var chartLabel =  this.getSeriesLabel(p);
			this.chart.setSeriesDisplay(chartLabel,false);
		}
		var chartLabel =  this.getSeriesLabel(index);
		this.chart.setSeriesDisplay(chartLabel,true);
		this.chart.chartTitle = ('Normalized Spectrum @ V=' + 
					this.series[0].points[index].toString() +
					', L='+this.series[0].lumi[index].toString()
					);
		this.chart.drawChart();
	}
};

/***************************************************************************
* line chart manager class
****************************************************************************/
function chartManager(legend,chartIDs,chartArgs){
	this.charts=[];
	for(var i=0;i<chartIDs.length;i++){
		newChart=new chartInstance(chartIDs[i],chartArgs[i]);
		this.charts.push(newChart);
	}

	this.legendCtrl=legend;
	$(this.legendCtrl).empty();

	this.legendSize=8;
}

chartManager.prototype.refresh=function(){
	for(var i=0;i<this.charts.length;i++)
		this.charts[i].drawChart();
}

chartManager.prototype.legendSymbol=function(shape,color,fill,size){
	var marginW=size;
	var marginH=size/2;
	var svgSym=document.createElementNS(window.svgns,'svg');
	svgSym.setAttributeNS(null,'id','lengendSVG');
	svgSym.setAttributeNS(null,'width',size+marginW);
	svgSym.setAttributeNS(null,'height',size+marginH);

	var svgShape=null
	if( shape == "circle"){
		svgShape=document.createElementNS(window.svgns,'circle');
		svgShape.setAttributeNS(null,'cx',size/2+marginW/2);
		svgShape.setAttributeNS(null,'cy',size/2+marginH/2);
		svgShape.setAttributeNS(null,'r',size/2);
	}
	else if(shape == "square"){
		svgShape=document.createElementNS(window.svgns,'rect');
		svgShape.setAttributeNS(null,'x',marginW/2);
		svgShape.setAttributeNS(null,'y',marginH/2);
		svgShape.setAttributeNS(null,'width',size);
		svgShape.setAttributeNS(null,'height',size);
	}
	else if(shape == "triangle"){
		svgShape=document.createElementNS(window.svgns,'polygon');
		var path=(size/2+marginW/2).toString()+','+(marginH/2).toString();
		path += ' ' + (marginW/2).toString()+','+(size+marginH/2).toString();
		path += ' ' + (size+marginW/2).toString()+','+(size+marginH/2).toString();
		svgShape.setAttributeNS(null,'points',path);
	}
	else if(shape == "triangle-down"){
		svgShape=document.createElementNS(window.svgns,'polygon');
		var path=(marginW/2).toString()+','+(marginH/2).toString();
		path += ' ' + (size+marginW/2).toString()+','+(marginH/2).toString();
		path += ' ' + (size/2+marginW/2).toString()+','+(size+marginH/2).toString();
		svgShape.setAttributeNS(null,'points',path);
	}
	else if(shape == "diamond"){
		svgShape=document.createElementNS(window.svgns,'polygon');
		var path=(size/2+marginW/2).toString()+','+(marginH/2).toString();
		path += ' ' + (marginW/2).toString()+','+(size/2+marginH/2).toString();
		path += ' ' + (size/2+marginW/2).toString()+','+(size+marginH/2).toString();
		path += ' ' + (size+marginW/2).toString()+','+(size/2+marginH/2).toString();
		svgShape.setAttributeNS(null,'points',path);
	}
	svgShape.setAttributeNS(null,'fill',fill);
	svgShape.setAttributeNS(null,'stroke',color);
	svgShape.setAttributeNS(null,'stroke-width','2');

	var line=document.createElementNS(window.svgns,'line');
	line.setAttributeNS(null,'x1',0);
	line.setAttributeNS(null,'y1',size/2+marginH/2);
	line.setAttributeNS(null,'x2',marginW+size);
	line.setAttributeNS(null,'y2',size/2+marginH/2);
	line.setAttributeNS(null,'stroke',color);
	line.setAttributeNS(null,'stroke-width','2');

	svgSym.appendChild(svgShape);
	svgSym.appendChild(line);
	return svgSym;

};

chartManager.prototype.setDataPlot=function(label,display){
	for(var i=0;i<this.charts.length;i++){
		this.charts[i].setSeriesDisplay(label,display);
		this.charts[i].drawChart();
	}
};

chartManager.prototype.addLegendItem=function(label,shape,color,fill){
		var listItem=document.createElement('li');
		listItem.setAttribute('id','legendItem');

		var ckBox=document.createElement('input');
		ckBox.setAttribute('type','checkbox');
		ckBox.setAttribute('class','legendCheck');
		ckBox.checked=true;
		ckBox.onclick=function(){
			var _label=label;
			window.chartManager.setDataPlot(_label,this.checked);
		};
		listItem.appendChild(ckBox);

		var symbol=this.legendSymbol(shape,color,fill,this.legendSize);
		listItem.appendChild(symbol);

		var name=document.createElement('span');
		name.innerHTML=label;
		listItem.appendChild(name);	

		var rm=document.createElement('a');
		rm.setAttribute('class','legendRemove');
		rm.innerHTML=' x';
		rm.onclick=function(){
			var _label=label;
			for(var i=0;i<window.chartManager.charts.length;i++)
				window.chartManager.charts[i].removeSeries(_label);
			window.spectrManager.removeSeries(_label);
			$(this).parent().remove();
		};
		listItem.appendChild(rm);	

		$(this.legendCtrl).append(listItem);
};

chartManager.prototype.clearSeries=function(){
	for(var i=0;i<this.charts.length;i++)
		this.charts[i].clearSeries();
	$(this.legendCtrl).empty();
};

chartManager.prototype.appendSeries=function(label,data,clear){
	if(clear)
		this.clearSeries();

	var check=this.charts[0].getLabelID(label);
	if((label != '') && (check==-1)) 
	{ // new series
		var legend=this.charts[0].getNextLegend();
		this.addLegendItem(label,legend.symbol,legend.color,legend.fill);
	}

	for(var i=0;i<this.charts.length;i++){
		this.charts[i].appendSeries(label,data[i],true);
		this.charts[i].drawChart();
	}

	return check;
};

/***************************************************************************
* line chart instance class
****************************************************************************/
function chartInstance(id,args){
	this.chartID=id;

	this.chartTitle="";
	this.xAxis={
		title:"",
		type:"linear"
	};
	this.yAxis={
		title:"",
		type:"linear",
		tickInterval:null,
		max:null
	};
	this.legend={
		layout:'horizontal',
        align: 'left',
		verticalAlign:'top',
		floating:true,
		x:70,
		y:30,
		margin:0,
		padding:0,
		enabled:false
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
chartInstance.prototype.setup=function(args){
	if(args.xAxisCtrl)
		this.xAxisCtrl=args.xAxisCtrl;
	this.yMaxCtrl=args.yMaxID;
	this.chartTitle=args.chartTitle;
	this.setXAxis(args.xTitle,args.xType);
	this.setYAxis(args.yTitle,args.yType,args.yMax,args.yTick);
	this.series=[];
	if(args.mouse != null)
		this.mouseTracking = args.mouse;
	else
		this.mouseTracking = true;
};
chartInstance.prototype.setXAxis=function(title,type){
	this.xAxis.title=title;
	this.xAxis.type=type;
};
chartInstance.prototype.setYAxis=function(title,type,max,tick){
	this.yAxis.title=title;
	this.yAxis.type=type;
	this.yAxis.max=max;
	this.yAxis.tickInterval=tick;
};

chartInstance.prototype.clearSeries=function(){
	this.series=[];
	this.drawChart();
};

// remove data series from line chart 
chartInstance.prototype.removeSeries=function(label){
	for(var i=0;i<this.series.length;i++)
		if(this.series[i].name == label)
			this.series.splice(i,1);
	this.drawChart();
};

// enable/disable the display of a specific data series 
chartInstance.prototype.setSeriesDisplay=function(label,display){
	for(var i=0;i<this.series.length;i++)
		if(this.series[i].name == label)
			this.series[i].display=display;	
	//this.drawChart();
};

// check if the specified data series already in the list 
chartInstance.prototype.getLabelID=function(label){
	for(var i=0;i<this.series.length;i++)
		if(this.series[i].name == label)
			return i;
	return -1;
};

// get the setting of next legend symbol
chartInstance.prototype.getNextLegend=function(){
	var legend={};
	legend.color =this.sColor [this.legendCnt % this.sColor.length ];
	legend.symbol=this.mSymbol[this.legendCnt % this.mSymbol.length];
	legend.fill  =this.sColor [this.legendCnt % this.sColor.length ];
	if(parseInt(this.series.length/this.mSymbol.length+0.9)%2)
		legend.fill='#FFFFFF';

	return legend;
};

// add new data series to the list 
chartInstance.prototype.appendSeries=function(label,data,display){
	if(label == null || label.length == 0)
		return;

	var index = this.getLabelID(label);
	if (index == -1){
		var legend=this.getNextLegend();
		newSeries={
			display:display,
			name:label,
			data:data,
			color:legend.color,
			enableMouseTracking:this.mouseTracking,
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

//	this.drawChart();
};

// draw the line chart 
chartInstance.prototype.drawChart=function(){
	var drawSeries=[];
	var yMax=null;
	if(this.yMaxCtrl != null)
		yMax=$(this.yMaxCtrl).val();

	if(this.xAxisCtrl)
		this.xAxis.type=$(this.xAxisCtrl).val();

	for (var i=0;i<this.series.length;i++)
		if(this.series[i].display)
			drawSeries.push(this.series[i]);

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
			type:this.xAxis.type
		},
        yAxis:{
            title: {text: this.yAxis.title},
			type:this.yAxis.type,
            plotLines: this.yAxis.plotLines,
			tickInterval:this.yAxis.tickInterval,
			max:yMax
        },
        legend:this.legend,
        series: drawSeries 
    };
	$(this.chartID).highcharts(chart);
};

