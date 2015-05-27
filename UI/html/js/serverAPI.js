window.config=[];
window.config.serverURL="http://192.168.1.65:8080/json"

function serverAPI (){
	this.log_msg="";
	this.err_log="";
}

serverAPI.prototype.log=function(msg){
	if (typeof msg == 'string'){
		var line='>'+msg+'\n';
		$('textarea#logConsole').append(line);
		$('textarea#logConsole').scrollTop($('textarea#logConsole')[0].scrollHeight);
	}
}

serverAPI.prototype.errCode=function(err){
	this.err_log += err;
}

serverAPI.prototype.post=function(json_args,callback){
	$.ajax({
		url:window.config.serverURL,
		type:"POST",
		data:{OTI_DATA:JSON.stringify(json_args)},
		success:function(result){
			if (result != 'NaN'){
				args=JSON.parse(result);
				server.errCode(args.errCode)
				server.log(args.logMsg);
				if (callback != null)
					callback(args.data);
			}
		}
	});
}
