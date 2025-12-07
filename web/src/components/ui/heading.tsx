import { cn } from "@/util/cn";
import React, { type HTMLAttributes } from "react";

type HeadingProps = {
  children: React.ReactNode;
} & HTMLAttributes<HTMLHeadingElement>;
const Heading = ({ children, className }: HeadingProps) => {
  return (
    <h1 className={cn("font-pixelated text-3xl", className)}>{children}</h1>
  );
};

export default Heading;
