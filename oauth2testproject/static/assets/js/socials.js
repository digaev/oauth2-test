$(document).ready(function() {
    $('.btn-social-icon').click(function(e) {
        var service_id = $(this).attr('service-id');
        if (service_id) {
            $.ajax({
                async: false,
                url: '/oauth2_auth?service=' + service_id,
                dataType: 'json'
            }).done(function(data, textStatus, jqXHR) {
                var w = 640;
                var h = 480;
                var x, y;
                try {
                    x = window.screen.width / 2 - w / 2;
                    y = window.screen.height / 2 - h / 2;
                } catch (e) {
                    x = y = 200;
                }

                return window.open(data.url, null,
                    'left=' + x +
                    ',top=' + y +
                    ',width=' + w +
                    ',height=' + h);
            })
        }
    });

    $('#btn-logout').click(function(e) {
        $(this).button('loading');
        $.ajax({
            async: false,
            url: '/signout'
        }).always(function(data, textStatus, jqXHR) {
            location.reload();
        });
    });
});
