var WS_URL="ws://{{server_name}}/foobar/";


var s = new WebSocket(WS_URL);
s.onopen = function() {
	alert("connected !!!");
	s.send("ciao");
};
s.onmessage = function(e) {
    var bb = document.getElementById('blackboard')
    var html = bb.innerHTML;
    bb.innerHTML = html + '<br/>' + e.data;
};
s.onerror = function(e) {
	alert(e);
}
s.onclose = function(e) {
	alert("connection closed");
}