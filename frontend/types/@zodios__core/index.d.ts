import type { z } from "zod";

declare module "@zodios/core" {
  export type ZodiosParameterType = "Body" | "Query" | "Path" | "Header";

  export type ZodiosEndpointDefinition = {
    method: string;
    path: string;
    alias?: string;
    description?: string;
    requestFormat?: string;
    response: z.ZodTypeAny;
    parameters?: Array<{
      name: string;
      type: ZodiosParameterType;
      schema: z.ZodTypeAny;
    }>;
    errors?: Array<{
      status: number;
      description?: string;
      schema: z.ZodTypeAny;
    }>;
  };

  export type ZodiosOptions = Record<string, unknown>;

  export function makeApi(...args: any[]): any;

  export class Zodios {
    constructor(...args: any[]);
  }
}
