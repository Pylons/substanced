(function() {

  $(function() {
    $('.tooltip-examples a, .tooltip-paragraph-examples a').tooltip({
      animation: false
    });
    $('.top-sign-in').on("click", function(e) {
      $('.login-box').fadeIn("fast");
      return false;
    });
    $('.login-box-close').on("click", function(e) {
      $(this).closest(".login-box").fadeOut("fast");
      return false;
    });
    prettyPrint();
    $(".slider-browser-center").animate({
      bottom: $(".slider-browser-center").data('position-bottom')
    }, "fast", function() {
      return $(".slider-browser-left").animate({
        bottom: $(".slider-browser-left").data('position-bottom')
      }, "fast", function() {
        return $(".slider-browser-right").animate({
          bottom: $(".slider-browser-right").data('position-bottom')
        }, "fast");
      });
    });
    $('.carousel').carousel({
      interval: false
    });
    return $('a[data-toggle="testimonial"]').on("click", function(e) {
      $(this).closest('.testimonials-users').find('a[data-toggle="testimonial"]').removeClass("active");
      $(this).addClass("active");
      $('.testimonials-speech').removeClass('active');
      $('.testimonials-speech' + $(this).attr('href')).addClass('active');
      return false;
    });
  });
  $("body").on("touchstart.dropdown", ".dropdown-menu", function(e) {
    return e.stopPropagation();
  });
  return $(document).on("click", ".dropdown-menu a", function() {
    return document.location = $(this).attr("href");
  });
}).call(this);
