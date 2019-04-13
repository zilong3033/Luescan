tasksdata=[]
$(document).ready(function(){
    $("#urls,#hosts").click(function(){
        source_type=$('input:radio[name="source_type"]:checked').val();
        if(source_type=="urls"){
            notice="输入格式:(127.0.0.1;http://zilong3033.cn)";
            $("#source").attr("placeholder",notice);
        }
        else{
            notice="输入格式:(127.0.0.1:88,192.168.1.1:80)";
            $("#source").attr("placeholder",notice);
        }
        console.log(source_type)
        $.post("/addsource",{
            source_type:source_type
        },
        function(data,status){
            var plugins_html="<form id='tasksps'>";
            for(var i in data){
                plugins_html+="<input type='checkbox' name='"+data[i]["name"]+"' values='"+data[i]["name"]+"'>"+data[i]["name"]+"<br>"
            }
            plugins_html+="</form>"
            $("#plugins_list").html(plugins_html)
            //console.log(data)
        });
    });

    //检测source规则
    function check_source(source_type,tasksname,source,plist){
        check_flag=1
        if(source.trim()!=""){
            if(source_type==="hosts"){
                sourcearry=source.trim().split(";")
                for(var i in sourcearry){
                    if(sourcearry[i]!=""&&sourcearry[i].indexOf(":")==-1){
                        check_flag=0
                    }
                }
                if(check_flag==0){
                    alert("目标格式不正确！");
                }
            }
        }
        else{
            check_flag=0
            alert("目标不能为空!")
        }
        if(plist.length==0){
            check_flag=0
            alert("没有选插件！")
        }
        if(tasksname==undefined){
            check_flag=0
            alert("任务名不能为空!")
        }
        else{
            if(tasksname.length==0){
                check_flag=0
                alert("任务名不能为空!")
            }
            if(tasksname.trim().length==0){
                check_flag=0
                alert("任务名不能为空!")
            }
        }
        return check_flag
    }

    $("#delpgs_submit").click(function(){
        data=$("#deleteplugins").serializeArray();
        data=JSON.stringify(data)
        console.log(data)
        $.post("/deleteplugins",{
            delplist:data
        },
        function(data,status){
            alert(data);
            location.reload()
        });
    });

    $(document).on("click","#btntasksps",function(){
        source_type=$('input:radio[name="source_type"]:checked').val();
        console.log(source_type)
        tasksname=$('#input1').val();
        source=$('#source').val();
        plist=$('#tasksps').serializeArray();
        plist=JSON.stringify(plist);
        check_flag=check_source(source_type,tasksname,source,plist)
        if(check_flag){
            //console.log(plist);
            $.post("/addtasks",{
                source_type:source_type,
                tasksname:tasksname,
                source,source,
                plist:plist
            },
            function(data,status){
                alert(data)
            });
        }
    });

    $('#uploadplugin').click(function(){
        var formData=new FormData();
        formData.append("file",$('#pluginsfile')[0].files[0])
        console.log(formData);
        $.ajax({
            url:"/plugins_upload",
            type:'POST',
            cache:false,
            data:formData,
            processData:false,
            contentType:false,
            success:function(data){
                alert(data);
                location.reload();
            }
        });
    });

    function gettasks(){
        $.get("/ptasklist",function(data,status){
            ptasklist_html="<table class='table table-hover'><caption>已完成的任务：</caption><thead><tr><th>展开</th><th style=' text-align:center'>任务号</th><th style=' text-align:center'>任务名</th><th style='text-align:center'>时间</th><th style='text-align:center' colspan='2'>操作</th></tr></thead><tbody>"
            //console.log(data)
            tasksdata=data
            start_pageid=1
            task_num=8
            for(var i in data){
                ptasklist_html+="<tr><td>+</td><td>"+data[i]["tasksid"]+"</td><td style='width: 178px'>"+"<a href='/presultlist/"+data[i]["tasksid"]+"'>"+data[i]["tasksname"]+"</a>"+"</td><td>"+data[i]["add_time"]+"</td><td><button class='btn btn-primary btn-xs' onclick='javascript:delpgstask("+tasksdata[i]["tasksid"]+")'><span class='glyphicon glyphicon-remove'></span></td><td><button class='btn btn-primary btn-xs' onclick='rerunptask("+tasksdata[i]["tasksid"]+")'><span class='glyphicon glyphicon-refresh'></span></td></tr>";
                if(i==task_num){
                    break;
                }
            }
            ptasklist_html+="</tbody></table>";
            pager_html="<ul class='pager'><li><a href='#'>Previous</a></li><li><a href='javascript:pagers(2)'>Next</a></li></ul>";
            ptasklist_html+=pager_html;
            $("#tasklist").html(ptasklist_html);
        });
    }

    function getps(){
        $.get("/pntask",function(data,status){
            ptasklist_html="<table class='table table-hover'><caption>正在进行的任务：</caption><thead><tr><th>展开</th><th style=' text-align:center'>任务号</th><th style=' text-align:center'>任务名</th><th style='text-align:center'>时间</th><th style='text-align:center'>进度</th><th style='text-align:center' colspan='2'>操作</th></tr></thead><tbody>"
            //console.log(data)
            for(var i in data){
                if(data[i]["is_stop"]==0)
                    ptasklist_html+="<tr><td>+</td><td>"+data[i]["tasksid"]+"</td><td>"+data[i]["tasksname"]+"</td><td>"+data[i]["add_time"]+"</td><td><a id="+data[i]["tasksid"]+">"+data[i]["ps"]+"</a></td><td><button class='btn btn-primary btn-xs' onclick='killtask("+data[i]["tasksid"]+")' id="+data[i]["tasksid"]+"><span class='glyphicon glyphicon-stop'></span></button></td><td><button class='btn btn-primary btn-xs' onclick='stoptask("+data[i]["tasksid"]+")' id="+data[i]["tasksid"]+"><span class='glyphicon glyphicon-pause'></span></button></td></tr>";
                else
                    ptasklist_html+="<tr><td>+</td><td>"+data[i]["tasksid"]+"</td><td>"+data[i]["tasksname"]+"</td><td>"+data[i]["add_time"]+"</td><td><a id="+data[i]["tasksid"]+">"+data[i]["ps"]+"</a></td><td><button class='btn btn-primary btn-xs' onclick='killtask("+data[i]["tasksid"]+")' id="+data[i]["tasksid"]+"><span class='glyphicon glyphicon-stop'></span></button></td><td><button class='btn btn-primary btn-xs' onclick='rerunptask("+data[i]["tasksid"]+")' id="+data[i]["tasksid"]+"><span class='glyphicon glyphicon-play'></span></button></td></tr>";
            }
            ptasklist_html+="</tbody></table>";
            $("#status").html(ptasklist_html);
            if(Object.keys(data).length!=0 && data[i]["is_finish"]==1){
                alert("任务完成");
                location.reload();
            }
        });
    }

    function default_geturl_plugin(){
        source_type=$('input:radio[name="source_type"]:checked').val();
        $.post("/addsource",{
            source_type:source_type
        },
        function(data,status){
            var plugins_html="<form id='tasksps'>";
            for(var i in data){
                plugins_html+="<input type='checkbox' name='"+data[i]["name"]+"' values='"+data[i]["name"]+"'>"+data[i]["name"]+"<br>"
            }
            plugins_html+="</form>"
            $("#plugins_list").html(plugins_html)
            //console.log(data)
        });
    }
    default_geturl_plugin();
    getps();
    gettasks();
    //setInterval(gettasks,1000);
    setInterval(getps,1000);
});

function delpgstask(id){
    url="/delpgstasks/"+id
    console.log(url)
    $.get(url,function(data,status){
        alert(data);
        location.reload()
    });
}

function pagers(pageid){
        task_num=8
        num=Object.keys(tasksdata).length
        if(pageid==0){
            return
        }
        ptasklist_html="<table class='table table-hover'><caption>已完成的任务：</caption><thead><tr><th>展开</th><th style=' text-align:center'>任务号</th><th style=' text-align:center'>任务名</th><th style='text-align:center'>时间</th><th style='text-align:center' colspan='2'>操作</th></tr></thead><tbody>"
        if(pageid<=Math.floor(num/task_num)){
            for(var i=(pageid-1)*task_num+1;i<=pageid*task_num;i++){
            console.log(i)
                ptasklist_html+="<tr><td>+</td><td>"+tasksdata[i]["tasksid"]+"</td><td style='width: 178px'>"+"<a href='/presultlist/"+tasksdata[i]["tasksid"]+"'>"+tasksdata[i]["tasksname"]+"</a>"+"</td><td>"+tasksdata[i]["add_time"]+"</td><td><button class='btn btn-primary btn-xs' onclick='javascript:delpgstask("+tasksdata[i]["tasksid"]+")'><span class='glyphicon glyphicon-remove'></span></td><td><button class='btn btn-primary btn-xs' onclick='rerunptask("+tasksdata[i]["tasksid"]+")'><span class='glyphicon glyphicon-refresh'></span></td></tr>";
            }
            ptasklist_html+="</tbody></table>";
            p_pageid=pageid-1
            n_pageid=pageid+1
            pager_html="<ul class='pager'><li><a href='javascript:pagers("+p_pageid+")'>Previous</a></li><li><a href='javascript:pagers("+n_pageid+")'>Next</a></li></ul>";
            ptasklist_html+=pager_html
            $("#tasklist").html(ptasklist_html);
        }else{
            for(var i=(pageid-1)*task_num+1;i<=num;i++){
                console.log(i)
                ptasklist_html+="<tr><td>+</td><td>"+tasksdata[i]["tasksid"]+"</td><td style='width: 178px'>"+"<a href='/presultlist/"+tasksdata[i]["tasksid"]+"'>"+tasksdata[i]["tasksname"]+"</a>"+"</td><td>"+tasksdata[i]["add_time"]+"</td><td><button class='btn btn-primary btn-xs' onclick='javascript:delpgstask("+tasksdata[i]["tasksid"]+")'><span class='glyphicon glyphicon-remove'></span></td><td><button class='btn btn-primary btn-xs' onclick='rerunptask("+tasksdata[i]["tasksid"]+")'><span class='glyphicon glyphicon-refresh'></span></td></tr>";
            }
            ptasklist_html+="</tbody></table>";
            p_pageid=pageid-1
            pager_html="<ul class='pager'><li><a href='javascript:pagers("+p_pageid+")'>Previous</a></li><li><a href='#'>Next</a></li></ul>";
            ptasklist_html+=pager_html
            $("#tasklist").html(ptasklist_html);
        }
}

function rerunptask(id){
    url="/rerunptasks/"+id
    $.get(url,function(data,status){
        location.reload();
    });
}

function stoptask(id){
    url="/stopptasks/"+id;
    $.get(url,function(data,status){
        if(data=="1"){
            alert("暂停成功！");
        }
    })
}

function killtask(id){
    url="/killtasks/"+id;
    $.get(url,function(data,status){
        alert(data);
        location.reload();
    });
}