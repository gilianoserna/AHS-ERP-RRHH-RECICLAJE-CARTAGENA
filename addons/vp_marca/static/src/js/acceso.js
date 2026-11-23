/** @odoo-module ignore **/
// Copyright ASH COLOMBIA SAS. Software propietario.
//
// La red de puntos de la pantalla de acceso: los colores del logo unidos por
// lineas finas que se acercan y se alejan, igual que la entrada de CONECTASH.
// Solo corre si hay un `canvas.vp_acceso_red` (la pantalla de acceso), se
// detiene sola con la pestaña oculta (requestAnimationFrame) y no corre si la
// persona pidio menos movimiento.
(function () {
    "use strict";
    function iniciar() {
        if (window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches) {
            return;
        }
        document.querySelectorAll("canvas.vp_acceso_red").forEach(function (cv) {
            var x = cv.getContext("2d");
            var col = ["#017DDB", "#5aa2ff", "#0EB9DA", "#FAB404", "#F20296", "#06B13E", "#E88C06"];
            var W, H, P = [], d = Math.min(2, window.devicePixelRatio || 1);
            function size() {
                var r = cv.getBoundingClientRect();
                W = r.width; H = r.height;
                cv.width = W * d; cv.height = H * d;
                x.setTransform(d, 0, 0, d, 0, 0);
                var n = Math.round(Math.max(18, Math.min(46, (W * H) / 14000)));
                P = [];
                for (var i = 0; i < n; i++) {
                    P.push({
                        x: Math.random() * W, y: Math.random() * H,
                        vx: (Math.random() - 0.5) * 0.25, vy: (Math.random() - 0.5) * 0.25,
                        r: i % 5 ? 1.6 : 3.2, c: col[i % col.length],
                    });
                }
            }
            function draw() {
                if (!cv.isConnected) { return; }
                x.clearRect(0, 0, W, H);
                for (var i = 0; i < P.length; i++) {
                    var a = P[i];
                    a.x += a.vx; a.y += a.vy;
                    if (a.x < 0 || a.x > W) { a.vx *= -1; }
                    if (a.y < 0 || a.y > H) { a.vy *= -1; }
                    for (var j = i + 1; j < P.length; j++) {
                        var b = P[j], s = Math.hypot(a.x - b.x, a.y - b.y);
                        if (s < 130) {
                            x.strokeStyle = "rgba(90,162,255," + (1 - s / 130) * 0.28 + ")";
                            x.lineWidth = 1;
                            x.beginPath(); x.moveTo(a.x, a.y); x.lineTo(b.x, b.y); x.stroke();
                        }
                    }
                }
                for (var k = 0; k < P.length; k++) {
                    var p = P[k];
                    x.fillStyle = p.c;
                    x.globalAlpha = p.r > 2 ? 0.95 : 0.6;
                    x.beginPath(); x.arc(p.x, p.y, p.r, 0, 7); x.fill();
                }
                x.globalAlpha = 1;
                requestAnimationFrame(draw);
            }
            window.addEventListener("resize", size);
            size();
            draw();
        });
    }
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", iniciar);
    } else {
        iniciar();
    }
})();
