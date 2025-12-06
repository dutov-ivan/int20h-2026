import { cn } from "@/util/cn";
import React, { type HTMLAttributes } from "react";

type WindowProps = {
  children?: React.ReactNode;
  handleColor: "light-blue" | "dark-blue";
  barColor: "light-blue" | "dark-blue";
} & HTMLAttributes<HTMLDivElement>;
const Window = ({
  children,
  handleColor,
  barColor,
  className,
  ...props
}: WindowProps) => {
  return (
    <div className={cn("bg-white", className)} {...props}>
      <div
        className={cn(
          "w-full px-1 py-2",
          barColor === "light-blue" ? "bg-accent" : "bg-light-blue",
          "flex items-center gap-1"
        )}
      >
        <div
          className={cn(
            "w-2 h-2 rounded-full",
            handleColor === "light-blue" ? "bg-accent" : "bg-light-blue"
          )}
        ></div>
        <div
          className={cn(
            "w-2 h-2 rounded-full",
            handleColor === "light-blue" ? "bg-accent" : "bg-light-blue"
          )}
        ></div>
        <div
          className={cn(
            "w-2 h-2 rounded-full",
            handleColor === "light-blue" ? "bg-accent" : "bg-light-blue"
          )}
        ></div>
      </div>
      {children}
    </div>
  );
};

export default Window;
