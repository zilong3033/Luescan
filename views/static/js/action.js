$(document).ready(function(){
    function update_check(){
        $.get("/upadate_check",function(data,status){
            $("#plugin_update_check").html(data)
        });
    }
    update_check();

    $("#update_plugins").click(function(){
        $.get("/pgsupdate",function(data,status){
            alert(data);
        });
    });
});

function delpgstask(id){
    url="/delpgstasks/"+id
    console.log(url)
    $.get(url,function(data,status){
        alert(data);
        location.reload()
    });
}

function reruntask(id){
    url="/reruntasks/"+id
    $.get(url,function(data,status){
        alert(data);
        window.location.href="/pluginscan";
    });
}

function logout(){
    url="/logout"
    $.get(url,function(data,status){
        window.location.href="/login";
    })
}

function rerunctask(tasksid){
    url="/rerunctask/"+tasksid
    $.get(url,function(data,status){
        alert(data);
        location.reload();
    });
}

function delclrtask(tasksid){
    url="/delclrtask/"+tasksid
    $.get(url,function(data,status){
        alert(data);
        location.reload();
    });
}