import type { IconType } from "react-icons";

interface StatCardProps {
  title: string;
  value: number;
  icon: IconType;
  iconColor: string;
  suffix?: string;
}

const StatCard = ({ title, value, icon: Icon, iconColor, suffix }: StatCardProps) => {
  return (
    <div className="bg-white flex flex-col items-stretch justify-between p-4 rounded-lg shadow-md w-full">
      <div className="flex items-center justify-between">
        <h3 className="text-sm text-gray-500 text-start capitalize">{title}</h3>
        <Icon className="h-10 w-10 bg-[var(--open-tickets-icon-bg)] p-2 rounded-lg" style={{ color: `var(--${iconColor})` }} />
      </div>
      <h2 className="text-2xl font-bold mt-2">{value} {suffix}</h2>
    </div>
  );
};

export default StatCard;
