import { cn } from "../utils/cn";

export function BackgroundGradientAnimation({
  children,
  className,
  containerClassName,
  animate = true,
}) {
  return (
    <div className={cn("relative overflow-hidden", containerClassName)}>
      <div className={cn("absolute inset-0 z-0", className)}>
        <div
          className={cn(
            "absolute top-0 left-[10%] w-[500px] h-[500px] bg-sage rounded-full mix-blend-multiply filter blur-3xl opacity-50",
            animate && "animate-first"
          )}
        />
        <div
          className={cn(
            "absolute bottom-0 right-[10%] w-[500px] h-[500px] bg-forest rounded-full mix-blend-multiply filter blur-3xl opacity-50",
            animate && "animate-second"
          )}
        />
        <div
          className={cn(
            "absolute top-[40%] right-[20%] w-[500px] h-[500px] bg-moss rounded-full mix-blend-multiply filter blur-3xl opacity-50",
            animate && "animate-third"
          )}
        />
        <div
          className={cn(
            "absolute bottom-[30%] left-[10%] w-[500px] h-[500px] bg-light-beige rounded-full mix-blend-multiply filter blur-3xl opacity-50",
            animate && "animate-fourth"
          )}
        />
        <div
          className={cn(
            "absolute top-[15%] right-[30%] w-[500px] h-[500px] bg-dark-forest rounded-full mix-blend-multiply filter blur-3xl opacity-50",
            animate && "animate-fifth"
          )}
        />
      </div>
      {children}
    </div>
  );
}
