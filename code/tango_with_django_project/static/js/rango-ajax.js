	$(document).ready(function() {
		// JQuery code to be added in here.
		$('#likes').click(function(){
		var catid;
		catid = $(this).attr("data-catid");
		$.get('/rango/like/', {category_id: catid}, function(data){
			$('#like_count').html(data);
			$('#likes').hide();
		});
	});




		$('#suggestion').keyup(function(){
		var query;
		query = $(this).val();
		$.get('/rango/suggest/', {suggestion: query}, function(data){
			$('#cats').html(data);
		});
	});

    $('.rango-add').click(function(){
	    var catid = $(this).attr("data-catid");
        var url = $(this).attr("data-url");
        var title = $(this).attr("data-title");
        var me = $(this)
	    $.get('/rango/add/', {category_id: catid, url: url, title: title}, function(data){
	                   $('#pages').html(data);
	                   me.hide();
	               });
	    });

	});
