
var STATUS = {
	{% for k, v in allStatus.items() %}
	{{k}}: {{v}},
	{% endfor %}
};

/*
 * usage:
 * 
 sleep(1000).then(() => {
	close_waiting_dialog();
})*/
var sleep = function (time) {
  return new Promise((resolve) => setTimeout(resolve, time));
}

var update_blackboard = function(msg){
	var bb = document.getElementById('blackboard')
	var html = bb.innerHTML;
	bb.innerHTML = html + '<br/>' + msg;
	bb.scrollTop = bb.scrollHeight;
};
