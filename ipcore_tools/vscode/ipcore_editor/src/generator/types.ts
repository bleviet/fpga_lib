/**
 * VHDL Generator Types
 * 
 * TypeScript interfaces for code generation data structures.
 */

/** Register field definition */
export interface RegisterField {
    name: string;
    offset: number;
    width: number;
    access: string;
    reset_value: number;
    description: string;
}

/** Register definition */
export interface Register {
    name: string;
    offset: number;
    access: string;
    description: string;
    fields: RegisterField[];
}

/** Generic/parameter definition */
export interface Generic {
    name: string;
    type: string;
    default_value: number | string | boolean | null;
}

/** User port definition */
export interface UserPort {
    name: string;
    direction: string;
    type: string;
}

/** Template context passed to Nunjucks */
export interface TemplateContext {
    entity_name: string;
    registers: Register[];
    generics: Generic[];
    user_ports: UserPort[];
    bus_type: string;
    data_width: number;
    addr_width: number;
    reg_width: number;
}

/** Generated file map */
export type GeneratedFiles = Map<string, string>;

/** Supported bus types */
export type BusType = 'axil' | 'avmm';
