load = function(){
//    setInterval(check, 2000);
    timeout = setTimeout(check, 100);
}

var check = function() {
    var xhr = new XMLHttpRequest();

    var first = document.body.getElementsByTagName("p")[0].getElementsByTagName("b")[0].innerHTML;

    //var da = first.split("GMT:")[0];

    xhr.open("GET", "/upd?date=" + first, true);

    xhr.onreadystatechange = function(){
        if (xhr.readyState == 4) {
            if (xhr.status == 200) {
                var resp = xhr.responseText;
                if (resp !== "") {
                    document.body.innerHTML = resp + document.body.innerHTML;
                }
            }
            load();
        }
    };

    xhr.send(null);
}
