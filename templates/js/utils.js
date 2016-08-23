/*
 * usage:
 * 
 sleep(1000).then(() => {
	close_waiting_dialog();
})*/
	
function sleep (time) {
  return new Promise((resolve) => setTimeout(resolve, time));
}