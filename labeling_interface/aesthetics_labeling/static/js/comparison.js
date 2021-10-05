function submitForm(code){
    console.log(code);
    document.getElementById("comparison_result").value = code;
    document.getElementById("main_form").submit();
}

document.addEventListener('keydown', function(event) {
 if(event.key === 'a'){
    submitForm(1);
 }else if(event.key === 'b'){
    submitForm(2);
 }else if(event.key === 's'){
    submitForm(3);
 }else if(event.key === 'd'){
    submitForm(4);
 }else if(event.key === 'f'){
    submitForm(5);
 }
});