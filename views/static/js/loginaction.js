$(document).ready(function(){
    $("#submit").click(function(){
         username=$("#username").val();
         password=$("#password").val();
        $.post("/login",
        {
            username:username,
            password:password
        },
        function(data,status){
            if(data=="index"){
                window.location.href="http://"+window.location.host;
            }
            else{
                alert("密码或者账户名错误!");
            }
        });
    });
});