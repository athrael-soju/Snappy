import type { ZodRecord, ZodString, ZodTypeAny } from "zod";

declare module "zod" {
  namespace z {
    function record<Value extends ZodTypeAny>(
      valueType: Value
    ): ZodRecord<ZodString, Value>;
  }
}
