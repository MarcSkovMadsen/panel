import { HTMLBox, HTMLBoxView } from "models/layouts/html_box"

// import { div } from "core/dom"
import * as p from "core/properties"

export class PxAppNavView extends HTMLBoxView {
    model: PxAppNav
    _element: Element

    initialize(): void {
        super.initialize()

        this._element = document.createElement("px-app-nav");
        this._element.setAttribute("items", this.model.items);
        this._element.innerHTML = this.model.items; // Todo: Remove
    }

    connect_signals(): void {
        super.connect_signals()

        this.connect(this.model.properties.items.change, () => this.render())
    }

    render(): void {
        super.render()

        if (!(this._element === this.el.childNodes[0])) {
            this.el.appendChild(this._element);
            console.log(this.el);
            console.log(this._element);
        }

        this._element.setAttribute("items", this.model.items);
        this._element.innerHTML = this.model.items; // Todo: Remove
    }
}

export namespace PxAppNav {
    export type Attrs = p.AttrsOf<Props>
    export type Props = HTMLBox.Props & {
        items: p.Property<string>
    }
}

export interface PxAppNav extends PxAppNav.Attrs { }

export class PxAppNav extends HTMLBox {
    properties: PxAppNav.Props

    constructor(attrs?: Partial<PxAppNav.Attrs>) {
        super(attrs)
    }

    static init_PxAppNav(): void {
        this.prototype.default_view = PxAppNavView;

        this.define<PxAppNav.Props>({
            items: [p.String, '{ "label": "Home", "id": "home", "icon": "px-fea:home" }'],
        })
    }
}
