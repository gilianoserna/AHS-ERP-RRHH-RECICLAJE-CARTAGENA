/** @odoo-module **/
// Copyright ASH COLOMBIA SAS. Software propietario.
//
// La cara del cliente web dice ASH ERP. Todo por los mecanismos de extension
// del propio Odoo —registros y `patch`—, sin tocar un archivo del motor.

import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { patch } from "@web/core/utils/patch";
import { NavBar } from "@web/webclient/navbar/navbar";
import {
    ClientErrorDialog,
    ErrorDialog,
    NetworkErrorDialog,
    RedirectWarningDialog,
    RPCErrorDialog,
    WarningDialog,
} from "@web/core/errors/error_dialogs";

export const MARCA = "ASH ERP";

/** Cambia el nombre del motor por el del producto en un titulo ya traducido. */
export function conMarca(texto) {
    return typeof texto === "string" || texto instanceof String
        ? String(texto).replace(/\bOdoo\b/g, MARCA)
        : texto;
}

// 1. El titulo de la pestaña.
//
// El servicio de titulo une las partes que ponen las pantallas («Ventas»,
// «S00012») y, si no hay ninguna, cae en «Odoo»
// (`web/static/src/core/browser/title_service.js:38`). Aqui la marca es
// SIEMPRE la ultima parte: «Ventas - ASH ERP», y «ASH ERP» a secas cuando
// no hay otra. Se borra y se vuelve a poner en cada cambio para que quede al
// final: el motor ordena las partes por orden de insercion.
export const marcaEnElTitulo = {
    dependencies: ["title"],
    start(env, { title }) {
        const ponerPartes = title.setParts;
        title.setParts = (partes) => {
            ponerPartes({ ...partes, vp_marca: undefined });
            ponerPartes({ vp_marca: MARCA });
        };
        title.setParts({});
    },
};
registry.category("services").add("vp_marca_titulo", marcaEnElTitulo);

// 2. El menu del usuario: fuera los dos enlaces al fabricante del motor.
//    «Ayuda» abre su centro de soporte y «Mi cuenta de Odoo.com» su portal.
//    El resto —atajos, preferencias, instalar la app, cerrar sesion— se queda.
//    Son las CLAVES del registro (`user_menu_items.js:139-145`), no el `id`
//    interno de cada entrada: la de la cuenta se registra como
//    "odoo_account" aunque su `id` sea "account". La primera version usaba el
//    `id` y la entrada seguia en pantalla; lo vio la verificacion en el
//    navegador.
export const ENLACES_DEL_MOTOR = ["support", "odoo_account"];
const menuUsuario = registry.category("user_menuitems");
for (const clave of ENLACES_DEL_MOTOR) {
    if (menuUsuario.contains(clave)) {
        menuUsuario.remove(clave);
    }
}

// 3. Los titulos de los dialogos de error: «Odoo Server Error»,
//    «Odoo Warning»... La traduccion puede decir «Error del servidor de
//    Odoo»; se cambia el nombre, no el resto del texto.
//
//    SE RESUELVEN AL MOSTRAR EL DIALOGO, NUNCA AL CARGAR ESTE ARCHIVO. Son
//    textos traducibles perezosos (`_t`) y convertirlos a texto aqui revienta
//    —«translations have not been loaded»—, porque este modulo se evalua
//    antes de que lleguen las traducciones. La primera version lo hacia asi
//    y tumbaba el cliente web entero: la pantalla quedaba en blanco. Lo
//    detecto la verificacion en el navegador, no las pruebas de Python.
for (const Dialogo of [ErrorDialog, ClientErrorDialog, NetworkErrorDialog]) {
    const original = Dialogo.title;
    Object.defineProperty(Dialogo, "title", {
        configurable: true,
        get: () => conMarca(String(original)),
    });
}
patch(RPCErrorDialog.prototype, {
    inferTitle() {
        super.inferTitle(...arguments);
        this.title = conMarca(this.title);
    },
});
patch(WarningDialog.prototype, {
    inferTitle() {
        return conMarca(super.inferTitle(...arguments));
    },
});
patch(RedirectWarningDialog.prototype, {
    setup() {
        super.setup(...arguments);
        this.title = conMarca(this.title);
    },
});

// 4. El logotipo de la barra superior (plantilla en `xml/marca.xml`): el de la
//    compañia ACTIVA en el selector. Sin el `company`, `/web/binary/company_logo`
//    sirve la compañia por defecto del usuario (`web/controllers/binary.py`).
//    `user.activeCompany` es como el propio cliente web la lee.
patch(NavBar.prototype, {
    get vpMarcaLogo() {
        const compania = user.activeCompany;
        return compania ? `/web/binary/company_logo?company=${compania.id}` : "/web/binary/company_logo";
    },
});
