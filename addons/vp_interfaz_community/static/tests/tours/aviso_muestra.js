/* Copyright ASH COLOMBIA SAS. Software propietario. */
/**
 * Que el aviso de datos de muestra se VEA de verdad, en un navegador.
 *
 * Las siete pruebas estructurales de `test_aviso_muestra.py` comprueban el
 * contrato con el upstream: que siga declarando `showRibbon`, que las cuatro
 * vistas sigan pasandolo, que la plantilla no cambie de nombre. Eso es
 * necesario y no es suficiente: **ninguna demuestra que el aviso llegue al
 * DOM**. Un error en el `xpath` de la herencia, un asset que no entra en el
 * bundle o un `t-if` mal escrito pasarian todas esas pruebas y dejarian al
 * usuario sin aviso.
 *
 * Estos dos recorridos cierran justo ese hueco, y son dos porque la propiedad
 * tiene dos caras: el aviso tiene que aparecer cuando los registros son
 * inventados y **no** aparecer cuando son reales. Un aviso que sale siempre no
 * avisa de nada.
 */
import { registry } from "@web/core/registry";

const AVISO = ".vp_aviso_muestra";
const TEXTO = "DATOS DE MUESTRA";

registry.category("web_tour.tours").add("vp_aviso_muestra_si", {
    steps: () => [
        {
            // La lista entra en `useSampleModel`: tiene `sample="1"` y el
            // dominio no devuelve ni un registro.
            trigger: ".o_list_view",
            run: () => {},
        },
        {
            // Y Odoo esta dibujando registros inventados, no una lista vacia.
            trigger: ".o_view_sample_data",
            run: () => {},
        },
        {
            trigger: `${AVISO}:visible`,
            run: () => {
                const aviso = document.querySelector(AVISO);
                if (!aviso) {
                    throw new Error("no hay aviso de datos de muestra en el DOM");
                }
                if (!aviso.textContent.includes(TEXTO)) {
                    throw new Error(`el aviso no dice «${TEXTO}»: ${aviso.textContent}`);
                }
                // Visible de verdad, no solo presente: un aviso con
                // `display:none` o de tamaño cero esta en el DOM y no avisa.
                const caja = aviso.getBoundingClientRect();
                if (caja.width < 50 || caja.height < 10) {
                    throw new Error(`el aviso esta en el DOM pero no se ve: ${JSON.stringify(caja)}`);
                }
                // Y una sola vez: si Odoo empezara a pintar su propio
                // RibbonWidget, el usuario veria dos avisos iguales.
                const cuantos = document.querySelectorAll(AVISO).length;
                if (cuantos !== 1) {
                    throw new Error(`hay ${cuantos} avisos y deberia haber 1`);
                }
            },
        },
    ],
});

registry.category("web_tour.tours").add("vp_aviso_muestra_no", {
    steps: () => [
        {
            // Misma vista, mismos assets, pero con datos reales.
            trigger: ".o_list_view .o_data_row",
            run: () => {},
        },
        {
            trigger: ".o_list_view",
            run: () => {
                if (document.querySelector(".o_view_sample_data")) {
                    throw new Error("con datos reales no deberia haber datos de muestra");
                }
                if (document.querySelector(AVISO)) {
                    throw new Error(
                        "el aviso sale con datos REALES: un aviso que sale siempre no avisa"
                    );
                }
            },
        },
    ],
});

/**
 * Y lo mismo en una GRAFICA, que es otro paquete de assets.
 *
 * Grafica y tabla dinamica viven en `web.assets_backend_lazy`, que no se carga
 * hasta que alguien abre una de esas vistas. Un error ahi —un nombre de
 * plantilla equivocado, por ejemplo— no se nota en una lista: aparece la primera
 * vez que un usuario abre una grafica. Eso es exactamente lo que estuvo a punto
 * de pasar: la herencia decia `web.GraphController` y la plantilla se llama
 * `web.GraphView`.
 */
registry.category("web_tour.tours").add("vp_aviso_muestra_grafica", {
    steps: () => [
        {
            trigger: ".o_graph_view",
            run: () => {},
        },
        {
            trigger: `${AVISO}:visible`,
            run: () => {
                const aviso = document.querySelector(AVISO);
                if (!aviso.textContent.includes(TEXTO)) {
                    throw new Error(`el aviso no dice «${TEXTO}»: ${aviso.textContent}`);
                }
                const cuantos = document.querySelectorAll(AVISO).length;
                if (cuantos !== 1) {
                    throw new Error(`hay ${cuantos} avisos en la grafica y deberia haber 1`);
                }
            },
        },
    ],
});
