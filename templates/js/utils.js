
var STATUS = {
	{% for st in all_status %}
	{{st.0}}: {{st.1}},
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
