import 'zodios';

declare module 'zodios' {
  interface ZodiosInstance {
    post<T extends unknown>(
      path: string,
      params?: Record<string, unknown>
    ): Promise<T>;
  }
}

