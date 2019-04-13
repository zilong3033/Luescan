function clrtaskslist(p_pageid){
    url="/clrtaskslist/"+p_pageid;
    $.get(url,function(data,status){
        n_pageid=data["n_pageid"]
        taskslist=data["page_tasks"]
        console.log(taskslist)
        ptasklist_html="<table class='table table-hover'><caption>已完成的任务：</caption><thead><tr><th>展开</th><th style=' text-align:center'>任务号</th><th style=' text-align:center'>任务名</th><th style='text-align:center'>时间</th><th style='text-align:center' colspan='2'>操作</th></tr></thead><tbody>";
        for(i in taskslist){
            if(taskslist[i]["p_run"]==1){
                ptasklist_html+="<tr><td>+</td><td>"+taskslist[i]["tasksid"]+"</td><td style='width: 178px'>"+"<a href='/cresultlist/"+taskslist[i]["tasksid"]+"'>"+taskslist[i]["tasksname"]+"</a>"+"</td><td>"+taskslist[i]["add_time"]+"</td><td><button class='btn btn-primary btn-xs' onclick='javascript:delclrtask("+taskslist[i]["tasksid"]+")'><span class='glyphicon glyphicon-remove'></span></td><td><button class='btn btn-primary btn-xs' onclick='rerunctask("+taskslist[i]["tasksid"]+")'><span class='glyphicon glyphicon-refresh'></span></td></tr>";
            }else{
                ptasklist_html+="<tr><td>+</td><td>"+taskslist[i]["tasksid"]+"</td><td style='width: 178px'>"+"<a id='atasksrun'>"+taskslist[i]["tasksname"]+"</a>"+"</td><td>"+taskslist[i]["add_time"]+"</td><td><button class='btn btn-primary btn-xs' onclick='javascript:delclrtask("+taskslist[i]["tasksid"]+")'><span class='glyphicon glyphicon-remove'></span></td><td><button class='btn btn-primary btn-xs' onclick='rerunctask("+taskslist[i]["tasksid"]+")'><span class='glyphicon glyphicon-refresh'></span></td></tr>";
            }
        }
        ptasklist_html+="</tbody></table>";
        if(p_pageid==0){
            pager_html="<ul class='pager'><li><a href='#'>Previous</a></li><li><a href='javascript:clrtaskslist("+n_pageid+")'>Next</a></li></ul>";
        }else{
            if(p_pageid-1!=-1){
                p_pageid=p_pageid-1
            }
            pager_html="<ul class='pager'><li><a href='javascript:clrtaskslist("+p_pageid+")'>Previous</a></li><li><a href='javascript:clrtaskslist("+n_pageid+")'>Next</a></li></ul>";
        }
        if(n_pageid=="#"){
            if(p_pageid-1!=-1){
                p_pageid=p_pageid-1
            }
            pager_html="<ul class='pager'><li><a href='javascript:clrtaskslist("+p_pageid+")'>Previous</a></li><li><a href='#'>Next</a></li></ul>";
        }
        ptasklist_html+=pager_html
        $("#tasks").html(ptasklist_html);
    });
}

function delclrtask(tasksid){
    url="/delclrtask/"+tasksid
    $.get(url,function(data,status){
        alert(data);
        location.reload();
    });
}

function rerunctask(tasksid){
    url="/rerunctask/"+tasksid
    $.get(url,function(data,status){
        alert(data);
        location.reload();
    });
}

function stopclrtask(tasksid){
    url="/stopclrtask/"+tasksid
    $.get(url,function(data,status){
        alert(data);
        location.reload();
    });
}

clrtaskslist(0)