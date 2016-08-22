
var _dialog_html = [
'<div class="modal fade" id="waiting-dialog-modal">', 
'  <div class="modal-dialog modal-sm" style="height: 150px; width: 150px;">', 
'    <div class="modal-content" style="border: none;">', 
'       <div id="loading">', 
'           <div id="loading-center">', 
'               <div id="loading-center-absolute">', 
'                   <div class="object" id="object_four"></div>', 
'                   <div class="object" id="object_three"></div>', 
'                   <div class="object" id="object_two"></div>', 
'                   <div class="object" id="object_one"></div>', 
'               </div>', 
'           </div>', 
'       </div>', 
'    </div>', 
'  </div>', 
'</div>'].join("");


var show_waiting_dialog = function(){
	$("body").append(_dialog_html);
	$("#waiting-dialog-modal").modal({
		backdrop: 'static',
		keyboard: false
	})
};

var close_waiting_dialog = function(){
	
};