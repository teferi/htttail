load = function(timeout){
    timeout = timeout || 100;
    var tid = setTimeout(check, timeout);
}

parse_response = function(text){
    var root = document.createElement("div");
    root.innerHTML = text;
    var elems = Array();
    for(var i=root.childNodes.length-1; i>=0; i--) {
        elems.push(root.childNodes[i]);
    }
    return elems;
}

var check = function() {
    var xhr = new XMLHttpRequest();
    var first = document.body.getElementsByTagName("p")[0].getElementsByTagName("b")[0].innerHTML;

    xhr.onreadystatechange = function(){
        if (xhr.readyState == 4) {
            if (xhr.status == 200) {
                var resp = xhr.responseText;
                if (resp !== "") {
                    var elems = parse_response(resp);
                    for (var i=0; i<elems.length; i++){
                        document.body.insertBefore(elems[i], document.body.firstChild);
                    }
                }
            }
            var timeout;
            if (xhr.status == 0) {
                timeout = 5000;
            }
            load(timeout);
        }
    };

    xhr.open("GET", "/upd?date=" + first, true);
    xhr.send(null);
}
