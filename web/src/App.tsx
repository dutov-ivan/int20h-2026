import "./index.css";
import Heading from "./components/ui/heading";

import logo from "@/assets/logo.svg";
import pixelButton from "@/assets/pixelated_button.png";
import uiCat from "@/assets/categories/ui.svg";
import webCat from "@/assets/categories/web.svg";
import devopsCat from "@/assets/categories/devops.svg";
import dsCat from "@/assets/categories/ds.svg";
import steps from "@/assets/how-participate/steps.png";
import arrows from "@/assets/how-participate/arrows.svg";
import heart1 from "@/assets/how-participate/heart1.svg";
import heart2 from "@/assets/how-participate/heart2.svg";
import heart3 from "@/assets/how-participate/heart3.svg";
import heart4 from "@/assets/how-participate/heart4.svg";
import StarEntry from "./components/StarEntry";
import Window from "./components/Window";

const App = () => {
  return (
    <div className="p-24">
      <div className="flex gap-16 justify-around">
        <img className="max-h-50" src={logo} alt="INT20H-2026 logo" />
        <div>
          <h2 className="font-bold text-lg">
            Ставай частинкою найбільшого студентського IT-хакатону в Україні!
          </h2>
          <p className="mt-4 text-sm">14-15 березня 2026, Київ</p>
          <p className="text-accent text-sm font-bold">Гібридний формат</p>
          <div className="relative max-w-80 min-w-60">
            <img className="absolute top-0 left-0" src={pixelButton} alt="" />
            <button className="relative mt-4 mx-auto block px-6 py-2 font-pixelated font-bold rounded-lg z-10">
              Registration
            </button>
          </div>
        </div>
      </div>
      <div className="mt-4">
        <Heading className="mb-4">INT20H Hackathon</Heading>
        <p className="font-black">20 годин. Практичний кейс. 1 шанс.</p>
        <p className="font-bold">
          Уже понад 10 років ми об’єднуємо молодих талановитих IT-розробників з
          усієї України. Студенти створюють інноваційні рішення, реалізують
          креативні ідеї, навчаються у провідних експертів та знаходять нові
          можливості для кар’єри.{" "}
        </p>
        <p className="font-black mt-4">
          Дати: <span className="text-accent">15-16 березня 2026 р.</span>
        </p>
        <p className="font-black">
          Формат: <span className="text-accent">гібрид*</span>
        </p>
        <p className="font-black">
          Місце: <span className="text-accent">Київ</span>
        </p>
        <p className="font-black">
          Команди: <span className="text-accent">2-4 особи</span>
        </p>
        <p className="text-sm font-black">
          * учасники матимуть можливість обрати формат своєї участі: offline або
          online
        </p>
      </div>
      <div className="mt-8">
        <Heading>Категорії</Heading>
        <div className="flex justify-between mt-4">
          <div className="flex flex-col items-center gap-2">
            <img className="w-24 h-24" src={uiCat} alt="UI/UX Design" />
            <p className="font-black">UI/UX Design</p>
          </div>
          <div className="flex flex-col items-center gap-2">
            <img className="w-24 h-24" src={webCat} alt="Web Development" />
            <p className="font-black">Web</p>
          </div>
          <div className="flex flex-col items-center gap-2">
            <img className="w-24 h-24" src={devopsCat} alt="DevOps" />
            <p className="font-black">DevOps</p>
          </div>
          <div className="flex flex-col items-center gap-2">
            <img className="w-24 h-24" src={dsCat} alt="Data Science" />
            <p className="font-black">Data Science</p>
          </div>
        </div>
      </div>

      <div className="mt-16">
        <Heading className="mb-8">Як взяти участь?</Heading>
        <img
          className="absolute mt-2 h-[550px] min-h-[550px] object-fill pr-48"
          src={steps}
          alt="How to participate steps"
        />
        <div className="pl-20 flex flex-col gap-11">
          <div className="flex justify-between items-center">
            <div className="flex gap-8 items-center">
              <img src={heart1} alt="Heart 1/4" className="w-12 h-12" />
              <p className="text-accent font-black">
                1. Реєструйся до xx.0x.2026 23:59
              </p>
            </div>
            <img className="max-w-50 mr-8" src={arrows} alt="Arrow" />
          </div>
          <div className="flex gap-8 items-center">
            <img src={heart2} alt="Heart 2/4" className="w-12 h-12" />
            <p className="text-accent font-black">
              2. Продемонструй свої скіли на відбірковому етапі дати
            </p>
          </div>
          <div className="flex justify-between">
            <div className="flex gap-8 items-center">
              <img src={heart3} alt="Heart 3/4" className="w-12 h-12" />
              <p className="text-accent font-black">
                3. Отримай запрошення до дати
              </p>
            </div>
            <img className="max-w-50 mr-8" src={arrows} alt="Arrow" />
          </div>
          <div className="flex gap-8 items-center">
            <img src={heart4} alt="Heart 4/4" className="w-12 h-12" />
            <p className="text-accent font-black">
              4. До зустрічі на основному етапі 15-16.03.2026
            </p>
          </div>
        </div>
      </div>
      <div className="mt-16">
        <Heading className="my-6">Що ти отримаєш?</Heading>
        <div className="grid grid-cols-2 grid-rows-3 gap-8">
          <StarEntry name="Пет-проєкт у твоє портфоліо" />
          <StarEntry name="Призи від партнерів" />
          <StarEntry name="Кар'єрні можливості" />
          <StarEntry name="Нетворкінг" />
          <StarEntry name="Нові скіли" />
          <StarEntry name="Смачні снеки" />
        </div>
      </div>

      <div className="mt-24">
        <Heading>Ментори та журі</Heading>
        <div className="flex flex-wrap gap-24 mt-8">
          <div className="flex flex-col gap-1 w-50">
            <Window
              className="w-50 h-50"
              handleColor="light-blue"
              barColor="dark-blue"
            ></Window>
            <p className="font-black">
              короткий опис експертів, які будуть допомагати та оцінювати
            </p>
          </div>
          <div className="flex flex-col gap-1 w-50">
            <Window
              className="w-50 h-50"
              handleColor="light-blue"
              barColor="dark-blue"
            ></Window>
            <p className="font-black">
              короткий опис експертів, які будуть допомагати та оцінювати
            </p>
          </div>
          <div className="flex flex-col gap-1 w-50">
            <Window
              className="w-50 h-50"
              handleColor="light-blue"
              barColor="dark-blue"
            ></Window>
            <p className="font-black">
              короткий опис експертів, які будуть допомагати та оцінювати
            </p>
          </div>
          <div className="flex flex-col gap-1 w-50">
            <Window
              className="w-50 h-50"
              handleColor="light-blue"
              barColor="dark-blue"
            ></Window>
            <p className="font-black">
              короткий опис експертів, які будуть допомагати та оцінювати
            </p>
          </div>
        </div>
      </div>

      <div>
        <Heading>Наші партнери</Heading>
      </div>

      <div>
        <Heading>Галерея</Heading>
      </div>
    </div>
  );
};

export default App;
