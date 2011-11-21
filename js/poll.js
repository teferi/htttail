load = function(){
//    setInterval(check, 2000);
    timeout = setTimeout(check, 100);
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

    //var da = first.split("GMT:")[0];

    xhr.open("GET", "/upd?date=" + first, true);

    xhr.onreadystatechange = function(){
        if (xhr.readyState == 4) {
            if (xhr.status == 200) {
                var resp = xhr.responseText;
                if (resp !== "") {
                    var elems = parse_response(resp);
                    for (var i=0; i<elems.length; i++){
                        document.body.insertBefore(elems[i], document.body.firstChild);
                    }
                    //document.body.innerHTML = resp + document.body.innerHTML;
                }
            }
            load();
        }
    };

    xhr.send(null);
}
