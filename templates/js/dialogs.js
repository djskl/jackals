
var _wait_dialog_html = [
'<div class="modal fade" id="waiting-dialog-modal" style="overflow: hidden;">', 
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
'			<div style="text-align: center; color: #901f3e; font-size: 18px;">正 在 提 交...</div>',
'       </div>', 
'    </div>', 
'  </div>', 
'</div>'].join("");

var show_waiting_dialog = function(){
	if($("#waiting-dialog-modal").length==0){
		$("body").append(_wait_dialog_html);
	}
	$("#waiting-dialog-modal").modal({
		backdrop: 'static',
		keyboard: false
	})
};

var close_waiting_dialog = function(){
	$('#waiting-dialog-modal').modal('hide');
};

var _error_dialog_html = [
'<div class="modal fade" id="error-dialog-modal">', 
'  <div class="modal-dialog">', 
'    <div class="modal-content">', 
'      <div class="modal-body" style="padding: 0px;">', 
'       <div class="alert alert-danger" style="margin-bottom: 0px;">', 
'         <button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">×</span></button>', 
'         <h4>__title__</h4>', 
'         <p>__details__</p>', 
'       </div>', 
'      </div>', 
'    </div>', 
'  </div>', 
'</div>'].join(""); 

var show_error_dialog = function(title, details){
	
	_error_dialog_html = _error_dialog_html.replace("__title__", title);
	_error_dialog_html = _error_dialog_html.replace("__details__", details);
	
	if($("#error-dialog-modal").length==0){
		$("body").append(_error_dialog_html);
	}
	
	$("#error-dialog-modal .alert-danger").bind('closed.bs.alert', function () {
		$("#error-dialog-modal").modal("hide");
    }); 
	
	$("#error-dialog-modal").modal();
	
};

