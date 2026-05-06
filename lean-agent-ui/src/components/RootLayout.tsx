import { Outlet } from "react-router-dom";
import { TopNav } from "./TopNav";

export function RootLayout() {
  return (
    <div className="grid h-screen grid-rows-[auto_1fr]">
      <TopNav />
      <div className="overflow-hidden">
        <Outlet />
      </div>
    </div>
  );
}
