import React from "react";
import star from "@/assets/star.png";

const StarEntry = ({ name }: { name: string }) => {
  return (
    <div className="flex gap-8 items-center">
      <img className="w-8 h-8" src={star} alt="Star bullet point" />
      <p className="text-accent-secondary font-black text-xl">{name}</p>
    </div>
  );
};

export default StarEntry;
