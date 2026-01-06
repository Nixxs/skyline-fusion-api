import {styled} from "@mui/material/styles";
import {Outlet} from "react-router-dom";

const Root = styled("div")(() => ({
    height: "100vh",    // Add this to lock the layout to the screen height
    width: "100vw",     // Optional: ensures no horizontal drift
}));

function Layout() {
    return (
        <Root>
          <Outlet />
        </Root>
    );
}

export default Layout;