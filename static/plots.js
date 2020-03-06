$(document).ready(function() {

    var next = $("#next")
    var previous =$("#previous")

    $(document).ready(function() {
    
        $(next).click(function () {
            $("ul").css({
                'margin-top' : '-303px' , 
                'transition' : 'all 1.5s ease-in-out'
            });

        });     

        $(previous).click(function () {
            $("ul").css("margin-top", "0");

        });

    });
});