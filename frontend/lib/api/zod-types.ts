import { z } from "zod";
import { schemas } from "@/lib/api/zod";

export type SearchItem = z.infer<typeof schemas.SearchItem>;
